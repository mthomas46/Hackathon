#!/usr/bin/env python3
"""
Comprehensive test script to validate all services after shared directory restructuring.

This script tests all services that use the shared directory to ensure they work
correctly with the new structure.
"""

import sys
import os
import importlib
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_service_imports():
    """Test all services that import from shared directory."""

    # Map of service directory names to their main module paths
    services_to_test = {
        'analysis-service': 'analysis-service.main',
        'doc_store': 'doc_store.main',
        'orchestrator': 'orchestrator.main',
        'source-agent': 'source_agent.main',
        'frontend': 'frontend.main',
        'interpreter': 'interpreter.main',
        'prompt-store': 'prompt_store.main',
        'prompt_store': 'prompt_store.main_new',
        'cli': 'cli.main',
        'notification-service': 'notification_service.main',
        'memory-agent': 'memory_agent.main',
        'discovery-agent': 'discovery_agent.main',
        'github-mcp': 'github_mcp.main',
        'bedrock-proxy': 'bedrock_proxy.main',
        'architecture-digitizer': 'architecture_digitizer.main',
        'summarizer-hub': 'summarizer_hub.main',
        'secure-analyzer': 'secure_analyzer.main',
        'code-analyzer': 'code_analyzer.main',
        'log-collector': 'log_collector.main',
    }

    results = {
        'passed': [],
        'failed': [],
        'skipped': []
    }

    print("🔍 Testing service imports after shared directory restructuring...\n")

    for service_name, module_path in services_to_test.items():
        print(f"Testing {service_name}...")

        try:
            # Handle special cases where module path needs adjustment
            if service_name == 'source-agent':
                module_path = 'source_agent.main'
            elif service_name == 'prompt-store':
                # Try both possible main files
                try:
                    importlib.import_module('prompt_store.main')
                    module_path = 'prompt_store.main'
                except ImportError:
                    module_path = 'prompt_store.main_new'

            # Import the main module
            module = importlib.import_module(module_path)

            # Try to get the main app object (FastAPI app, etc.)
            app = getattr(module, 'app', None)
            if app is None:
                # Some services might use different naming
                app = getattr(module, 'application', None)
            if app is None:
                app = getattr(module, 'main', None)

            if app is not None:
                results['passed'].append(service_name)
                print(f"  ✅ {service_name} imports successfully")
            else:
                results['failed'].append((service_name, "No main app object found"))
                print(f"  ❌ {service_name} - No main app object found")

        except ImportError as e:
            results['failed'].append((service_name, f"Import error: {e}"))
            print(f"  ❌ {service_name} - Import error: {e}")

        except Exception as e:
            results['failed'].append((service_name, f"Unexpected error: {e}"))
            print(f"  ❌ {service_name} - Unexpected error: {e}")
            if '--verbose' in sys.argv:
                traceback.print_exc()

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

    return results

def main():
    """Main entry point."""
    results = test_service_imports()

    # Exit with error code if any tests failed
    if results['failed']:
        sys.exit(1)

if __name__ == "__main__":
    main()
