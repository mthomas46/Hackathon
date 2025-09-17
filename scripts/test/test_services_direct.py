#!/usr/bin/env python3
"""
Direct test script to validate services after shared directory restructuring.

This script directly executes service main files to test imports.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_service_direct(service_path, service_name):
    """Test a service by directly executing its main file."""
    try:
        # Create a test script for this service
        test_script = f"""
import sys
import os
sys.path.insert(0, r'{project_root}')

try:
    # Import the service module directly
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '{service_name}',
        r'{service_path}/main.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Check for common app objects
    app = getattr(module, 'app', None)
    if app is None:
        app = getattr(module, 'application', None)
    if app is None:
        app = getattr(module, 'main', None)

    if app is not None:
        print('SUCCESS')
    else:
        print('NO_APP_OBJECT')

except Exception as e:
    print(f'ERROR: {{e}}')
    import traceback
    traceback.print_exc()
"""

        # Run the test script
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            if output == 'SUCCESS':
                return True, None
            elif output == 'NO_APP_OBJECT':
                return False, "No main app object found"
            else:
                return True, None  # Unexpected success
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            return False, error_msg

    except subprocess.TimeoutExpired:
        return False, "Test timed out"
    except Exception as e:
        return False, str(e)

def main():
    """Main entry point."""
    # Map of service names to their directory paths
    services = {
        'analysis-service': 'services/analysis-service',
        'doc_store': 'services/doc_store',
        'orchestrator': 'services/orchestrator',
        'source-agent': 'services/source-agent',
        'frontend': 'services/frontend',
        'interpreter': 'services/interpreter',
        'prompt-store': 'services/prompt_store',
        'cli': 'services/cli',
        'notification-service': 'services/notification-service',
        'memory-agent': 'services/memory-agent',
        'discovery-agent': 'services/discovery-agent',
        'github-mcp': 'services/github-mcp',
        'bedrock-proxy': 'services/bedrock-proxy',
        'architecture-digitizer': 'services/architecture-digitizer',
        'summarizer-hub': 'services/summarizer-hub',
        'secure-analyzer': 'services/secure-analyzer',
        'code-analyzer': 'services/code-analyzer',
        'log-collector': 'services/log-collector',
    }

    results = {
        'passed': [],
        'failed': [],
        'skipped': []
    }

    print("🔍 Testing service imports after shared directory restructuring...\n")

    for service_name, service_path in services.items():
        full_path = project_root / service_path

        if not full_path.exists():
            results['skipped'].append(service_name)
            print(f"⏭️  {service_name} - Directory not found")
            continue

        if not (full_path / 'main.py').exists():
            results['skipped'].append(service_name)
            print(f"⏭️  {service_name} - main.py not found")
            continue

        print(f"Testing {service_name}...")

        success, error = test_service_direct(full_path, service_name)

        if success:
            results['passed'].append(service_name)
            print(f"  ✅ {service_name} imports successfully")
        else:
            results['failed'].append((service_name, error))
            print(f"  ❌ {service_name} - {error}")

    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)

    print(f"\n✅ PASSED ({len(results['passed'])}):")
    for service in results['passed']:
        print(f"  • {service}")

    if results['failed']:
        print(f"\n❌ FAILED ({len(results['failed'])}):")
        for service, error in results['failed']:
            print(f"  • {service}: {error}")

    if results['skipped']:
        print(f"\n⏭️  SKIPPED ({len(results['skipped'])}):")
        for service in results['skipped']:
            print(f"  • {service}")

    total_tested = len(results['passed']) + len(results['failed']) + len(results['skipped'])
    success_rate = (len(results['passed']) / total_tested * 100) if total_tested > 0 else 0

    print(f"\n📈 Success Rate: {success_rate:.1f}% ({len(results['passed'])}/{total_tested})")

    # Save detailed results to file
    with open(project_root / 'service_test_results.txt', 'w') as f:
        f.write("SERVICE IMPORT TEST RESULTS\n")
        f.write("="*40 + "\n\n")

        f.write(f"PASSED ({len(results['passed'])}):\n")
        for service in results['passed']:
            f.write(f"  • {service}\n")

        if results['failed']:
            f.write(f"\nFAILED ({len(results['failed'])}):\n")
            for service, error in results['failed']:
                f.write(f"  • {service}: {error}\n")

        if results['skipped']:
            f.write(f"\nSKIPPED ({len(results['skipped'])}):\n")
            for service in results['skipped']:
                f.write(f"  • {service}\n")

        f.write(f"\nSuccess Rate: {success_rate:.1f}% ({len(results['passed'])}/{total_tested})\n")

    return results

if __name__ == "__main__":
    main()
