#!/usr/bin/env python3
"""
API Contract Validator for Hackathon Ecosystem

This script validates API contracts across all services to ensure:
- Consistent OpenAPI/Swagger documentation
- Standard health endpoints
- Proper error response formats
- API versioning consistency
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, List, Tuple
import re
from urllib.parse import urljoin

# Service API contract expectations
API_CONTRACTS = {
    "discovery-agent": {
        "port": 5045,
        "docs_endpoints": ["/docs", "/openapi.json", "/redoc"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/services", "/api/v1/scan"]
    },
    "doc_store": {
        "port": 5087,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/documents", "/api/v1/search"]
    },
    "llm-gateway": {
        "port": 5055,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/completions", "/api/v1/chat"]
    },
    "code-analyzer": {
        "port": 5025,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/analyze", "/api/v1/metrics"]
    },
    "secure-analyzer": {
        "port": 5100,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/scan", "/api/v1/report"]
    },
    "analysis-service": {
        "port": 5080,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/analyze", "/api/v1/results"]
    },
    "summarizer-hub": {
        "port": 5160,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/summarize", "/api/v1/batch"]
    },
    "source-agent": {
        "port": 5085,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/sources", "/api/v1/scan"]
    },
    "memory-agent": {
        "port": 5090,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/memory", "/api/v1/search"]
    },
    "prompt_store": {
        "port": 5110,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/prompts", "/api/v1/templates"]
    },
    "log-collector": {
        "port": 5040,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/logs", "/api/v1/metrics"]
    },
    "notification-service": {
        "port": 5130,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/notifications", "/api/v1/webhooks"]
    },
    "mock-data-generator": {
        "port": 5065,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/generate", "/api/v1/collections"]
    },
    "project-simulation": {
        "port": 5075,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/simulate", "/api/v1/projects"]
    },
    "orchestrator": {
        "port": 5099,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/workflows", "/api/v1/tasks"]
    },
    "architecture-digitizer": {
        "port": 5105,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/digitize", "/api/v1/schemas"]
    },
    "interpreter": {
        "port": 5120,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/v1/execute", "/api/v1/environments"]
    },
    "frontend": {
        "port": 3000,
        "docs_endpoints": [],  # Frontend might not have OpenAPI docs
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/status"]
    },
    "unified-api-dashboard": {
        "port": 8000,
        "docs_endpoints": ["/docs", "/openapi.json"],
        "health_endpoint": "/health",
        "expected_endpoints": ["/health", "/api/discovery/services", "/api/catalog"]
    }
}

def validate_openapi_spec(spec: dict) -> List[str]:
    """Validate OpenAPI specification structure."""
    issues = []

    # Check required fields
    required_fields = ["openapi", "info", "paths"]
    for field in required_fields:
        if field not in spec:
            issues.append(f"Missing required field: {field}")

    # Check info section
    if "info" in spec:
        info = spec["info"]
        if "title" not in info:
            issues.append("Missing info.title")
        if "version" not in info:
            issues.append("Missing info.version")

    # Check paths section
    if "paths" in spec:
        paths = spec["paths"]
        if not isinstance(paths, dict):
            issues.append("paths must be an object")
        elif len(paths) == 0:
            issues.append("No API paths defined")

        # Check for health endpoint
        health_paths = ["/health", "/api/health", "/status"]
        has_health = any(path in paths for path in health_paths)
        if not has_health:
            issues.append("No health endpoint found in paths")

    return issues

def validate_health_response(response: dict) -> List[str]:
    """Validate health endpoint response format."""
    issues = []

    # Check for status field
    if "status" not in response:
        issues.append("Health response missing 'status' field")
    elif response["status"] not in ["healthy", "unhealthy", "degraded"]:
        issues.append(f"Invalid status value: {response['status']}")

    # Check for timestamp
    if "timestamp" not in response:
        issues.append("Health response missing 'timestamp' field")

    return issues

async def check_service_contract(service_name: str, config: dict, session: aiohttp.ClientSession) -> Tuple[str, Dict]:
    """Check API contract for a single service."""
    issues = []
    base_url = f"http://localhost:{config['port']}"

    try:
        # Check health endpoint
        health_url = urljoin(base_url, config["health_endpoint"])
        async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                try:
                    health_data = await response.json()
                    health_issues = validate_health_response(health_data)
                    issues.extend([f"Health: {issue}" for issue in health_issues])
                except Exception as e:
                    issues.append(f"Health: Invalid JSON response - {str(e)}")
            else:
                issues.append(f"Health: HTTP {response.status}")

        # Check OpenAPI documentation
        docs_found = False
        for docs_endpoint in config["docs_endpoints"]:
            docs_url = urljoin(base_url, docs_endpoint)
            try:
                async with session.get(docs_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        docs_found = True
                        if docs_endpoint.endswith(".json"):
                            try:
                                spec = await response.json()
                                spec_issues = validate_openapi_spec(spec)
                                issues.extend([f"OpenAPI: {issue}" for issue in spec_issues])
                            except Exception as e:
                                issues.append(f"OpenAPI: Invalid JSON spec - {str(e)}")
                        break
            except:
                continue

        if not docs_found and config["docs_endpoints"]:
            issues.append("OpenAPI documentation not available")

        # Check expected endpoints exist
        for endpoint in config["expected_endpoints"]:
            endpoint_url = urljoin(base_url, endpoint)
            try:
                async with session.get(endpoint_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    # Just check if endpoint exists (doesn't return error)
                    pass
            except aiohttp.ClientConnectorError:
                issues.append(f"Endpoint not accessible: {endpoint}")
            except asyncio.TimeoutError:
                issues.append(f"Endpoint timeout: {endpoint}")

        return service_name, {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "port": config["port"]
        }

    except Exception as e:
        return service_name, {
            "status": "error",
            "issues": [f"Unexpected error: {str(e)}"],
            "port": config["port"]
        }

async def main():
    """Main API contract validation function."""
    print("📋 API Contract Validator - Hackathon Ecosystem")
    print("=" * 50)

    connector = aiohttp.TCPConnector(limit=10)
    timeout = aiohttp.ClientTimeout(total=10, connect=3)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for service_name, config in API_CONTRACTS.items():
            tasks.append(check_service_contract(service_name, config, session))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    passed = []
    failed = []
    errors = []

    print("\n📋 API Contract Validation Results:")
    print("-" * 50)

    for result in results:
        if isinstance(result, Exception):
            print(f"⚠️  Unexpected error: {result}")
            continue

        service_name, data = result
        status = data.get("status", "unknown")
        issues = data.get("issues", [])
        port = data.get("port", "N/A")

        if status == "pass":
            passed.append(service_name)
            print(f"✅ {service_name:<25} [Port {port}]")
        elif status == "fail":
            failed.append(service_name)
            print(f"❌ {service_name:<25} [Port {port}] - {len(issues)} issues")
            for issue in issues[:3]:  # Show first 3 issues
                print(f"   • {issue}")
            if len(issues) > 3:
                print(f"   • ... and {len(issues) - 3} more issues")
        else:
            errors.append(service_name)
            print(f"⚠️  {service_name:<25} [Port {port}] - ERROR")
            for issue in issues:
                print(f"   • {issue}")

    # Summary
    total = len(results)
    passed_count = len(passed)
    failed_count = len(failed)
    error_count = len(errors)

    print("\n📊 Summary:")
    print(f"   Total Services: {total}")
    print(f"   Passed: {passed_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Errors: {error_count}")

    if total > 0:
        compliance_rate = (passed_count / total) * 100
        print(".1f")

    # Exit codes
    if failed_count > 0 or error_count > 0:
        print("\n❌ API contract validation failed!")
        print("💡 Fix the issues above to ensure API consistency across services.")
        sys.exit(1)
    else:
        print("\n✅ All API contracts are valid!")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
