#!/usr/bin/env python3
"""Comprehensive test runner for the Discovery Agent new features.

This script runs all tests for the enhanced Discovery Agent without
relying on complex import path issues.
"""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_unit_tests():
    """Run unit tests for individual components."""
    print("🧪 Running Unit Tests")
    print("=" * 50)
    
    passed = 0
    total = 0
    
    # Test 1: Tool Registry Module
    print("\n📚 Testing Tool Registry...")
    try:
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
            
        # Import and test the tool registry
        sys.path.insert(0, str(project_root / 'services' / 'discovery-agent'))
        from modules.tool_registry import ToolRegistryStorage
        
        # Test basic operations
        registry = ToolRegistryStorage(temp_file)
        
        # Test save and load
        test_data = {
            "timestamp": "2025-01-17T21:30:00Z",
            "services_tested": 2,
            "total_tools_discovered": 3,
            "services": {
                "service1": {"tools": [{"name": "tool1", "category": "read"}]},
                "service2": {"tools": [{"name": "tool2", "category": "write"}]}
            }
        }
        
        registry.save_discovery_results(test_data)
        
        # Verify data was saved
        loaded_registry = ToolRegistryStorage(temp_file)
        assert len(loaded_registry.registry["discovery_runs"]) == 1
        assert loaded_registry.registry["discovery_runs"][0]["total_tools_discovered"] == 3
        
        # Test stats
        stats = loaded_registry.get_registry_stats()
        assert "last_updated" in stats
        
        # Cleanup
        os.unlink(temp_file)
        
        print("✅ Tool Registry tests passed")
        passed += 1
        
    except Exception as e:
        print(f"❌ Tool Registry tests failed: {e}")
    
    total += 1
    
    # Test 2: Monitoring Service
    print("\n📊 Testing Monitoring Service...")
    try:
        from modules.monitoring_service import DiscoveryAgentMonitoring
        
        monitoring = DiscoveryAgentMonitoring()
        
        # Test logging
        initial_count = len(monitoring.events)
        monitoring.log_discovery_event("test_event", {"test": "data"})
        assert len(monitoring.events) > initial_count
        
        # Test dashboard creation
        dashboard = monitoring.create_monitoring_dashboard()
        assert "dashboard_title" in dashboard
        assert "discovery_events_count" in dashboard
        
        print("✅ Monitoring Service tests passed")
        passed += 1
        
    except Exception as e:
        print(f"❌ Monitoring Service tests failed: {e}")
    
    total += 1
    
    # Test 3: Performance Optimizer
    print("\n⚡ Testing Performance Optimizer...")
    try:
        from modules.performance_optimizer import PerformanceOptimizer
        
        optimizer = PerformanceOptimizer()
        
        # Test performance optimization
        test_data = {
            "services_tested": 3,
            "healthy_services": 3,
            "total_tools_discovered": 15,
            "performance_metrics": [
                {"service": "service1", "response_time": 1.2, "tools_found": 5},
                {"service": "service2", "response_time": 0.8, "tools_found": 3},
                {"service": "service3", "response_time": 2.5, "tools_found": 7}
            ]
        }
        
        result = optimizer.optimize_discovery_workflow(test_data)
        assert "optimizations" in result
        assert "performance_summary" in result
        
        # Test dependency analysis
        tools = [
            {"name": "tool1", "category": "storage", "capabilities": ["storage"]},
            {"name": "tool2", "category": "analysis", "capabilities": ["analysis"]}
        ]
        
        dependencies = optimizer.analyze_tool_dependencies(tools)
        assert "dependency_graph" in dependencies
        assert "independent_tools" in dependencies
        
        print("✅ Performance Optimizer tests passed")
        passed += 1
        
    except Exception as e:
        print(f"❌ Performance Optimizer tests failed: {e}")
    
    total += 1
    
    # Test 4: Security Scanner
    print("\n🔒 Testing Security Scanner...")
    try:
        from modules.security_scanner import ToolSecurityScanner
        
        scanner = ToolSecurityScanner()
        
        # Test mock security report generation
        test_tool = {
            "name": "test_delete_tool",
            "service": "test-service",
            "method": "DELETE",
            "path": "/api/delete",
            "description": "Delete resource tool"
        }
        
        # Test the mock security report generation
        report = scanner._generate_mock_security_report(test_tool)
        assert "overall_risk" in report
        assert "vulnerabilities" in report
        assert "recommendations" in report
        
        print("✅ Security Scanner tests passed")
        passed += 1
        
    except Exception as e:
        print(f"❌ Security Scanner tests failed: {e}")
    
    total += 1
    
    # Test 5: AI Tool Selector
    print("\n🤖 Testing AI Tool Selector...")
    try:
        from modules.ai_tool_selector import AIToolSelector
        
        selector = AIToolSelector()
        
        # Test rule-based task analysis
        analysis = selector._rule_based_task_analysis("analyze documents and create reports")
        assert "primary_action" in analysis
        assert "data_types" in analysis
        assert "capabilities" in analysis
        
        # Test tool scoring
        test_tool = {
            "name": "doc_analyzer",
            "category": "analysis",
            "method": "POST",
            "description": "Analyze documents"
        }
        
        task_analysis = {"primary_action": "analyze", "data_types": ["documents"], "capabilities": ["analysis"]}
        score = selector._calculate_tool_score(test_tool, task_analysis)
        assert "total_score" in score
        assert score["total_score"] > 0
        
        print("✅ AI Tool Selector tests passed")
        passed += 1
        
    except Exception as e:
        print(f"❌ AI Tool Selector tests failed: {e}")
    
    total += 1
    
    # Test 6: Semantic Analyzer
    print("\n🧠 Testing Semantic Analyzer...")
    try:
        from modules.semantic_analyzer import SemanticToolAnalyzer
        
        analyzer = SemanticToolAnalyzer()
        
        # Test rule-based semantic analysis
        test_tool = {
            "name": "document_analyzer",
            "category": "analysis",
            "description": "Analyze document content for insights",
            "method": "POST",
            "path": "/analyze"
        }
        
        result = analyzer._rule_based_semantic_analysis(test_tool)
        assert "semantic_categories" in result
        assert "primary_category" in result
        assert "capabilities_identified" in result
        
        print("✅ Semantic Analyzer tests passed")
        passed += 1
        
    except Exception as e:
        print(f"❌ Semantic Analyzer tests failed: {e}")
    
    total += 1
    
    return passed, total


def run_integration_tests():
    """Run integration tests between modules."""
    print("\n🔗 Running Integration Tests")
    print("=" * 50)
    
    passed = 0
    total = 0
    
    # Integration Test 1: Registry + Monitoring
    print("\n📊 Testing Registry + Monitoring Integration...")
    try:
        from modules.tool_registry import ToolRegistryStorage
        from modules.monitoring_service import DiscoveryAgentMonitoring
        
        # Create temporary registry
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        registry = ToolRegistryStorage(temp_file)
        monitoring = DiscoveryAgentMonitoring()
        
        # Test workflow: Discovery -> Registry -> Monitoring
        discovery_data = {
            "timestamp": "2025-01-17T21:30:00Z",
            "services_tested": 2,
            "total_tools_discovered": 4,
            "services": {
                "service1": {"tools": [{"name": "tool1", "category": "read"}]},
                "service2": {"tools": [{"name": "tool2", "category": "write"}]}
            }
        }
        
        # Save to registry
        registry.save_discovery_results(discovery_data)
        
        # Log to monitoring
        monitoring.log_discovery_event("discovery_complete", {
            "services": 2,
            "tools": 4,
            "status": "success"
        })
        
        # Verify integration
        assert len(registry.registry["discovery_runs"]) == 1
        assert len(monitoring.events) > 0
        
        # Cleanup
        os.unlink(temp_file)
        
        print("✅ Registry + Monitoring integration passed")
        passed += 1
        
    except Exception as e:
        print(f"❌ Registry + Monitoring integration failed: {e}")
    
    total += 1
    
    # Integration Test 2: AI Selector + Performance Optimizer
    print("\n🤖 Testing AI Selector + Performance Optimizer Integration...")
    try:
        from modules.ai_tool_selector import AIToolSelector
        from modules.performance_optimizer import PerformanceOptimizer
        
        selector = AIToolSelector()
        optimizer = PerformanceOptimizer()
        
        # Test workflow: Tool Selection -> Performance Analysis
        available_tools = [
            {"name": "tool1", "category": "storage", "capabilities": ["storage"]},
            {"name": "tool2", "category": "analysis", "capabilities": ["analysis"]},
            {"name": "tool3", "category": "processing", "capabilities": ["processing"]}
        ]
        
        # Select tools
        task_analysis = selector._rule_based_task_analysis("store and analyze data")
        tool_scores = selector._score_tools_for_task(task_analysis, available_tools)
        selected_tools = selector._select_optimal_tools(tool_scores, task_analysis)
        
        # Analyze performance
        dependencies = optimizer.analyze_tool_dependencies(selected_tools)
        
        # Verify integration
        assert len(selected_tools) > 0
        assert "dependency_graph" in dependencies
        
        print("✅ AI Selector + Performance Optimizer integration passed")
        passed += 1
        
    except Exception as e:
        print(f"❌ AI Selector + Performance Optimizer integration failed: {e}")
    
    total += 1
    
    return passed, total


def run_functional_tests():
    """Run functional tests for end-to-end workflows."""
    print("\n🎯 Running Functional Tests")
    print("=" * 50)
    
    passed = 0
    total = 0
    
    # Functional Test 1: Complete Discovery Workflow
    print("\n🔍 Testing Complete Discovery Workflow...")
    try:
        from modules.tool_registry import ToolRegistryStorage
        from modules.monitoring_service import DiscoveryAgentMonitoring
        from modules.performance_optimizer import PerformanceOptimizer
        from modules.security_scanner import ToolSecurityScanner
        
        # Create temporary registry
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        registry = ToolRegistryStorage(temp_file)
        monitoring = DiscoveryAgentMonitoring()
        optimizer = PerformanceOptimizer()
        scanner = ToolSecurityScanner()
        
        # Simulate discovery workflow
        discovery_results = {
            "timestamp": "2025-01-17T21:30:00Z",
            "services_tested": 3,
            "healthy_services": 3,
            "total_tools_discovered": 6,
            "performance_metrics": [
                {"service": "service1", "response_time": 1.0, "tools_found": 2},
                {"service": "service2", "response_time": 1.5, "tools_found": 2},
                {"service": "service3", "response_time": 0.8, "tools_found": 2}
            ],
            "services": {
                "service1": {"tools": [
                    {"name": "service1_read", "category": "read", "method": "GET"},
                    {"name": "service1_write", "category": "write", "method": "POST"}
                ]},
                "service2": {"tools": [
                    {"name": "service2_analyze", "category": "analysis", "method": "POST"},
                    {"name": "service2_store", "category": "storage", "method": "POST"}
                ]},
                "service3": {"tools": [
                    {"name": "service3_delete", "category": "delete", "method": "DELETE"},
                    {"name": "service3_query", "category": "query", "method": "GET"}
                ]}
            }
        }
        
        # Step 1: Store discovery results
        registry.save_discovery_results(discovery_results)
        
        # Step 2: Log to monitoring
        monitoring.log_discovery_event("ecosystem_discovery", {
            "services_tested": 3,
            "tools_discovered": 6,
            "performance_summary": "completed successfully"
        })
        
        # Step 3: Optimize performance
        optimization_results = optimizer.optimize_discovery_workflow(discovery_results)
        
        # Step 4: Security scan (mock)
        all_tools = []
        for service_data in discovery_results["services"].values():
            all_tools.extend(service_data["tools"])
        
        security_reports = []
        for tool in all_tools:
            report = scanner._generate_mock_security_report(tool)
            security_reports.append(report)
        
        # Verify complete workflow
        assert len(registry.registry["discovery_runs"]) == 1
        assert len(monitoring.events) > 0
        assert "optimizations" in optimization_results
        assert len(security_reports) == 6
        
        # Cleanup
        os.unlink(temp_file)
        
        print("✅ Complete Discovery Workflow passed")
        passed += 1
        
    except Exception as e:
        print(f"❌ Complete Discovery Workflow failed: {e}")
        import traceback
        traceback.print_exc()
    
    total += 1
    
    return passed, total


def main():
    """Run all tests."""
    print("🚀 Discovery Agent New Features Test Suite")
    print("=" * 60)
    
    total_passed = 0
    total_tests = 0
    
    # Run unit tests
    unit_passed, unit_total = run_unit_tests()
    total_passed += unit_passed
    total_tests += unit_total
    
    # Run integration tests
    integration_passed, integration_total = run_integration_tests()
    total_passed += integration_passed
    total_tests += integration_total
    
    # Run functional tests
    functional_passed, functional_total = run_functional_tests()
    total_passed += functional_passed
    total_tests += functional_total
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 FINAL TEST RESULTS: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Discovery Agent new features are working perfectly!")
        return True
    else:
        failed_tests = total_tests - total_passed
        print(f"❌ {failed_tests} tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
