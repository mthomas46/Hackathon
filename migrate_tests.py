#!/usr/bin/env python3
"""
Test Migration Script - Migrate tests from global /tests directory to service DDD test directories
"""

import os
import shutil
from pathlib import Path

def get_service_test_mapping():
    """Map global test directories to service DDD test directories"""
    return {
        'analysis_service': 'services/analysis-service/tests',
        'bedrock_proxy': 'services/bedrock-proxy/tests', 
        'cli': 'services/cli/tests',
        'code_analyzer': 'services/code-analyzer/tests',
        'discovery_agent': 'services/discovery-agent/tests',
        'doc_store': 'services/doc_store/tests',
        'frontend': 'services/frontend/tests',
        'github_mcp': 'services/github-mcp/tests',
        'interpreter': 'services/interpreter/tests',
        'llm_gateway': 'services/llm-gateway/tests',
        'log_collector': 'services/log-collector/tests',
        'memory_agent': 'services/memory-agent/tests',
        'notification_service': 'services/notification-service/tests',
        'orchestrator': 'services/orchestrator/tests',
        'prompt_store': 'services/prompt_store/tests',
        'secure_analyzer': 'services/secure-analyzer/tests',
        'shared': 'services/shared/tests',
        'source_agent': 'services/source-agent/tests',
        'summarizer_hub': 'services/summarizer-hub/tests',
    }

def migrate_unit_tests():
    """Migrate unit tests from tests/unit/ to service test directories"""
    unit_tests_dir = Path('tests/unit')
    mapping = get_service_test_mapping()
    
    print("🔄 Migrating unit tests...")
    
    for service_name, service_test_dir in mapping.items():
        if service_name in ['project-simulation']:  # Skip services that don't follow naming convention
            continue
            
        global_service_tests = unit_tests_dir / service_name
        if global_service_tests.exists():
            service_test_path = Path(service_test_dir)
            
            # Ensure service test directory exists
            service_test_path.mkdir(parents=True, exist_ok=True)
            (service_test_path / 'unit').mkdir(exist_ok=True)
            
            print(f"  📁 Migrating {service_name} unit tests...")
            
            # Copy all test files
            for item in global_service_tests.rglob('*'):
                if item.is_file() and (item.name.startswith('test_') or item.name == 'conftest.py'):
                    relative_path = item.relative_to(global_service_tests)
                    dest_path = service_test_path / 'unit' / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(item, dest_path)
                    print(f"    ✅ {relative_path} → {dest_path}")

def migrate_integration_tests():
    """Migrate integration tests from tests/integration/ to service test directories"""
    integration_tests_dir = Path('tests/integration')
    mapping = get_service_test_mapping()
    
    print("\\n🔄 Migrating integration tests...")
    
    for service_name, service_test_dir in mapping.items():
        global_service_tests = integration_tests_dir / service_name
        if global_service_tests.exists():
            service_test_path = Path(service_test_dir)
            
            # Ensure service test directory exists
            service_test_path.mkdir(parents=True, exist_ok=True)
            (service_test_path / 'integration').mkdir(exist_ok=True)
            
            print(f"  📁 Migrating {service_name} integration tests...")
            
            # Copy all test files
            for item in global_service_tests.rglob('*'):
                if item.is_file() and (item.name.startswith('test_') or item.name == 'conftest.py'):
                    relative_path = item.relative_to(global_service_tests)
                    dest_path = service_test_path / 'integration' / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(item, dest_path)
                    print(f"    ✅ {relative_path} → {dest_path}")

def migrate_cli_tests():
    """Migrate CLI-specific tests"""
    cli_tests_dir = Path('tests/cli')
    cli_service_test_dir = Path('services/cli/tests')
    
    print("\\n🔄 Migrating CLI tests...")
    
    # Ensure CLI test directory exists
    cli_service_test_dir.mkdir(parents=True, exist_ok=True)
    
    for item in cli_tests_dir.rglob('*'):
        if item.is_file() and (item.name.startswith('test_') or item.name == 'conftest.py'):
            relative_path = item.relative_to(cli_tests_dir)
            dest_path = cli_service_test_dir / relative_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(item, dest_path)
            print(f"  ✅ {relative_path} → {dest_path}")

def migrate_performance_tests():
    """Migrate performance tests to appropriate service directories"""
    perf_tests_dir = Path('tests/performance')
    mapping = get_service_test_mapping()
    
    print("\\n🔄 Migrating performance tests...")
    
    for item in perf_tests_dir.glob('test_*_performance.py'):
        # Extract service name from filename
        filename = item.name
        service_name = None
        
        if 'api' in filename:
            service_name = 'shared'  # Generic API tests
        elif 'document_persistence' in filename:
            service_name = 'doc_store'
        elif 'prompt_store' in filename:
            service_name = 'prompt_store'
        elif 'redis' in filename:
            service_name = 'shared'  # Redis is shared infrastructure
        elif 'advanced_ecosystem' in filename:
            service_name = 'shared'  # Ecosystem-wide tests
        
        if service_name and service_name in mapping:
            service_test_path = Path(mapping[service_name])
            service_test_path.mkdir(parents=True, exist_ok=True)
            (service_test_path / 'performance').mkdir(exist_ok=True)
            
            dest_path = service_test_path / 'performance' / item.name
            shutil.copy2(item, dest_path)
            print(f"  ✅ {item.name} → {service_name}/performance/")

def create_ddd_test_structure():
    """Create DDD test directory structure for services that don't have it"""
    mapping = get_service_test_mapping()
    
    print("\\n🔄 Creating DDD test structures...")
    
    for service_name, service_test_dir in mapping.items():
        service_test_path = Path(service_test_dir)
        
        # Create standard DDD test structure
        (service_test_path / 'unit').mkdir(parents=True, exist_ok=True)
        (service_test_path / 'integration').mkdir(parents=True, exist_ok=True)
        (service_test_path / 'performance').mkdir(parents=True, exist_ok=True)
        (service_test_path / 'e2e').mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files
        for subdir in ['unit', 'integration', 'performance', 'e2e']:
            init_file = service_test_path / subdir / '__init__.py'
            if not init_file.exists():
                init_file.write_text(f'"""Tests for {service_name} {subdir} layer."""\\n')
        
        # Create main conftest.py if it doesn't exist
        conftest_file = service_test_path / 'conftest.py'
        if not conftest_file.exists():
            conftest_file.write_text(f'''"""Test configuration for {service_name} service."""

import pytest
import sys
from pathlib import Path

# Add service path for imports
service_path = Path(__file__).parent
sys.path.insert(0, str(service_path))

# Add shared services path
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))
''')
        
        print(f"  ✅ Created DDD test structure for {service_name}")

def main():
    """Main migration function"""
    print("🚀 Starting test migration to DDD service directories...")
    print("=" * 60)
    
    # Create DDD test structures first
    create_ddd_test_structure()
    
    # Migrate tests by category
    migrate_unit_tests()
    migrate_integration_tests()
    migrate_cli_tests()
    migrate_performance_tests()
    
    print("\\n" + "=" * 60)
    print("✅ Test migration completed!")
    print("\\n📋 Next steps:")
    print("  1. Review migrated tests for import path updates")
    print("  2. Update any hardcoded paths in test files")
    print("  3. Run tests to ensure they work in new locations")
    print("  4. Remove old test files from global /tests directory")
    print("  5. Update CI/CD pipelines to use new test locations")

if __name__ == '__main__':
    main()
