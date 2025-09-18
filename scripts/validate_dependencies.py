#!/usr/bin/env python3
"""
Dependency Validation Script
Validates that all required dependencies are installed and working correctly.
"""

import sys
import importlib
from typing import List, Dict, Any

# Core dependencies that must be installed
REQUIRED_DEPS = [
    'redis',
    'requests',
    'aiohttp',
    'yaml',
    'docker',
    'click',
    'rich',
    'psutil',
    'prometheus_client',
    'structlog',
    'pandas',
    'numpy'
]

# Optional dependencies
OPTIONAL_DEPS = [
    'kubernetes',
    'boto3',
    'grafana_api',
    'sentry_sdk',
    'matplotlib'
]

def check_dependency(name: str, required: bool = True) -> Dict[str, Any]:
    """Check if a dependency is installed and get version info."""
    try:
        module = importlib.import_module(name)
        version = getattr(module, '__version__', 'unknown')
        return {
            'name': name,
            'installed': True,
            'version': version,
            'error': None
        }
    except ImportError as e:
        status = 'MISSING' if required else 'OPTIONAL'
        return {
            'name': name,
            'installed': False,
            'version': None,
            'error': str(e),
            'status': status
        }

def validate_core_functionality():
    """Test core functionality that depends on the installed packages."""
    results = {}

    # Test Redis connection (if Redis is running)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        results['redis_connection'] = {'status': 'OK', 'message': 'Redis connection successful'}
    except Exception as e:
        results['redis_connection'] = {'status': 'WARN', 'message': f'Redis connection failed: {e}'}

    # Test HTTP requests
    try:
        import requests
        # Use a more reliable test endpoint
        response = requests.get('https://httpbin.org/status/200', timeout=10)
        results['http_requests'] = {'status': 'OK', 'message': f'HTTP request successful (status: {response.status_code})'}
    except Exception as e:
        # Fallback to a simpler test
        try:
            import urllib.request
            with urllib.request.urlopen('https://httpbin.org/status/200', timeout=10) as response:
                results['http_requests'] = {'status': 'OK', 'message': f'HTTP request successful (status: {response.status})'}
        except Exception as e2:
            results['http_requests'] = {'status': 'ERROR', 'message': f'HTTP request failed: {e}, fallback also failed: {e2}'}

    # Test YAML parsing
    try:
        import yaml
        test_data = yaml.safe_load('key: value\nlist:\n  - item1\n  - item2')
        results['yaml_parsing'] = {'status': 'OK', 'message': 'YAML parsing successful'}
    except Exception as e:
        results['yaml_parsing'] = {'status': 'ERROR', 'message': f'YAML parsing failed: {e}'}

    # Test Docker client (if Docker is available)
    try:
        import docker
        # Try different ways to create Docker client
        try:
            client = docker.from_env()
            client.ping()
        except AttributeError:
            # Fallback for different Docker versions
            client = docker.Client()
            client.ping()
        results['docker_client'] = {'status': 'OK', 'message': 'Docker client connection successful'}
    except Exception as e:
        results['docker_client'] = {'status': 'WARN', 'message': f'Docker client failed: {e}'}

    return results

def main():
    """Main validation function."""
    print("🔍 LLM Documentation Ecosystem - Dependency Validation")
    print("=" * 60)

    # Check required dependencies
    print("\n📦 Checking Required Dependencies:")
    required_results = []
    for dep in REQUIRED_DEPS:
        result = check_dependency(dep, required=True)
        required_results.append(result)
        if result['installed']:
            print(f"  ✅ {result['name']} (v{result['version']})")
        else:
            print(f"  ❌ {result['name']} - MISSING: {result['error']}")

    # Check optional dependencies
    print("\n🔧 Checking Optional Dependencies:")
    optional_results = []
    for dep in OPTIONAL_DEPS:
        result = check_dependency(dep, required=False)
        optional_results.append(result)
        if result['installed']:
            print(f"  ✅ {result['name']} (v{result['version']})")
        else:
            print(f"  ⚠️  {result['name']} - OPTIONAL: Not installed")

    # Validate core functionality
    print("\n🧪 Testing Core Functionality:")
    functionality_results = validate_core_functionality()
    for test_name, result in functionality_results.items():
        status_icon = {
            'OK': '✅',
            'WARN': '⚠️',
            'ERROR': '❌'
        }.get(result['status'], '❓')
        print(f"  {status_icon} {test_name}: {result['message']}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")

    required_missing = [r for r in required_results if not r['installed']]
    optional_installed = [r for r in optional_results if r['installed']]

    if required_missing:
        print(f"❌ CRITICAL: {len(required_missing)} required dependencies missing")
        print("   Please install missing dependencies:")
        for dep in required_missing:
            print(f"   pip install {dep['name']}")
    else:
        print("✅ All required dependencies installed")

    print(f"🔧 Optional dependencies installed: {len(optional_installed)}/{len(OPTIONAL_DEPS)}")

    # Check functionality
    errors = [r for r in functionality_results.values() if r['status'] == 'ERROR']
    warnings = [r for r in functionality_results.values() if r['status'] == 'WARN']

    if errors:
        print(f"❌ Functionality errors: {len(errors)}")
    else:
        print("✅ Core functionality working")

    if warnings:
        print(f"⚠️  Functionality warnings: {len(warnings)}")

    # Exit code
    if required_missing or errors:
        print("\n❌ VALIDATION FAILED - Please fix issues above")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED - All dependencies working correctly")
        sys.exit(0)

if __name__ == "__main__":
    main()
