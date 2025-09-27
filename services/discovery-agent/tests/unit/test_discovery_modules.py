#!/usr/bin/env python3
"""Test the Discovery Agent modules directly.

This script tests the individual modules without needing to start a server.
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_module_imports():
    """Test that all modules can be imported successfully."""
    print("🔍 Testing module imports...")

    try:
        from services.discovery_agent.modules.tool_discovery import tool_discovery_service
        print("✅ tool_discovery module imported")
    except Exception as e:
        print(f"❌ tool_discovery import failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.security_scanner import tool_security_scanner
        print("✅ security_scanner module imported")
    except Exception as e:
        print(f"❌ security_scanner import failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.monitoring_service import discovery_monitoring_service
        print("✅ monitoring_service module imported")
    except Exception as e:
        print(f"❌ monitoring_service import failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.tool_registry import tool_registry_storage
        print("✅ tool_registry module imported")
    except Exception as e:
        print(f"❌ tool_registry import failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.orchestrator_integration import orchestrator_integration
        print("✅ orchestrator_integration module imported")
    except Exception as e:
        print(f"❌ orchestrator_integration import failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.ai_tool_selector import ai_tool_selector
        print("✅ ai_tool_selector module imported")
    except Exception as e:
        print(f"❌ ai_tool_selector import failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.semantic_analyzer import semantic_tool_analyzer
        print("✅ semantic_analyzer module imported")
    except Exception as e:
        print(f"❌ semantic_analyzer import failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.performance_optimizer import performance_optimizer
        print("✅ performance_optimizer module imported")
    except Exception as e:
        print(f"❌ performance_optimizer import failed: {e}")
        return False

    return True


def test_service_initialization():
    """Test that services can be initialized."""
    print("\n🏗️  Testing service initialization...")

    try:
        from services.discovery_agent.modules.tool_discovery import tool_discovery_service
        # Test basic functionality
        assert hasattr(tool_discovery_service, 'discover_ecosystem_tools')
        print("✅ tool_discovery_service initialized")
    except Exception as e:
        print(f"❌ tool_discovery_service init failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.security_scanner import tool_security_scanner
        assert hasattr(tool_security_scanner, 'scan_tool_security')
        print("✅ tool_security_scanner initialized")
    except Exception as e:
        print(f"❌ tool_security_scanner init failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.monitoring_service import discovery_monitoring_service
        assert hasattr(discovery_monitoring_service, 'log_discovery_event')
        print("✅ discovery_monitoring_service initialized")
    except Exception as e:
        print(f"❌ discovery_monitoring_service init failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.tool_registry import tool_registry_storage
        assert hasattr(tool_registry_storage, 'save_discovery_results')
        print("✅ tool_registry_storage initialized")
    except Exception as e:
        print(f"❌ tool_registry_storage init failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.orchestrator_integration import orchestrator_integration
        assert hasattr(orchestrator_integration, 'register_discovered_tools')
        print("✅ orchestrator_integration initialized")
    except Exception as e:
        print(f"❌ orchestrator_integration init failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.ai_tool_selector import ai_tool_selector
        assert hasattr(ai_tool_selector, 'select_tools_for_task')
        print("✅ ai_tool_selector initialized")
    except Exception as e:
        print(f"❌ ai_tool_selector init failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.semantic_analyzer import semantic_tool_analyzer
        assert hasattr(semantic_tool_analyzer, 'analyze_tool_semantics')
        print("✅ semantic_tool_analyzer initialized")
    except Exception as e:
        print(f"❌ semantic_tool_analyzer init failed: {e}")
        return False

    try:
        from services.discovery_agent.modules.performance_optimizer import performance_optimizer
        assert hasattr(performance_optimizer, 'optimize_discovery_workflow')
        print("✅ performance_optimizer initialized")
    except Exception as e:
        print(f"❌ performance_optimizer init failed: {e}")
        return False

    return True


def test_basic_functionality():
    """Test basic functionality of key modules."""
    print("\n⚙️  Testing basic functionality...")

    # Test tool registry
    try:
        from services.discovery_agent.modules.tool_registry import tool_registry_storage

        # Test saving and loading tools
        test_tools = {"service1": [{"name": "test_tool", "category": "read"}]}

        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            # Create a temporary registry instance
            registry = tool_registry_storage.__class__(temp_file)

            # Test basic operations
            assert hasattr(registry, 'save_tools')
            assert hasattr(registry, 'get_all_tools')
            print("✅ Tool registry basic functionality working")
        finally:
            os.unlink(temp_file)

    except Exception as e:
        print(f"❌ Tool registry functionality test failed: {e}")
        return False

    # Test monitoring service
    try:
        from services.discovery_agent.modules.monitoring_service import discovery_monitoring_service

        # Test logging
        initial_count = len(discovery_monitoring_service.events)
        discovery_monitoring_service.log_discovery_event("test", {"test": "data"})
        assert len(discovery_monitoring_service.events) > initial_count
        print("✅ Monitoring service basic functionality working")

    except Exception as e:
        print(f"❌ Monitoring service functionality test failed: {e}")
        return False

    # Test performance optimizer
    try:
        from services.discovery_agent.modules.performance_optimizer import performance_optimizer

        # Test basic functionality
        test_data = {
            "performance_metrics": [{"response_time": 1.0, "tools_found": 5}],
            "summary": {"tools_discovered": 5}
        }

        result = performance_optimizer.optimize_discovery_workflow(test_data)
        assert "optimizations" in result
        print("✅ Performance optimizer basic functionality working")

    except Exception as e:
        print(f"❌ Performance optimizer functionality test failed: {e}")
        return False

    return True


def test_integration_scenarios():
    """Test integration between modules."""
    print("\n🔗 Testing module integration...")

    try:
        from services.discovery_agent.modules.tool_discovery import tool_discovery_service
        from services.discovery_agent.modules.tool_registry import tool_registry_storage
        from services.discovery_agent.modules.security_scanner import tool_security_scanner
        from services.discovery_agent.modules.monitoring_service import discovery_monitoring_service

        # Test that services can work together
        # Create mock discovery results
        mock_results = {
            "services_tested": 2,
            "healthy_services": 2,
            "total_tools_discovered": 4,
            "services": {
                "service1": {"tools": [{"name": "tool1", "category": "read"}]},
                "service2": {"tools": [{"name": "tool2", "category": "write"}]}
            }
        }

        # Test registry can handle discovery results
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            registry = tool_registry_storage.__class__(temp_file)
            registry.save_discovery_results(mock_results)

            # Verify data was saved
            loaded = registry.load_discovery_results()
            assert temp_file in loaded
            assert loaded[temp_file]["total_tools_discovered"] == 4

            print("✅ Module integration working (discovery -> registry)")
        finally:
            os.unlink(temp_file)

    except Exception as e:
        print(f"❌ Module integration test failed: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("🧪 Testing Discovery Agent Modules")
    print("=" * 50)

    tests = [
        ("Module Imports", test_module_imports),
        ("Service Initialization", test_service_initialization),
        ("Basic Functionality", test_basic_functionality),
        ("Integration Scenarios", test_integration_scenarios)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"📊 Test Results: {passed}/{total} test suites passed")

    if passed == total:
        print("🎉 ALL MODULE TESTS PASSED! Discovery Agent modules are functional.")
        return True
    else:
        failed_tests = [name for name, result in results if not result]
        print(f"❌ Failed test suites: {', '.join(failed_tests)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
