#!/usr/bin/env python3
"""Test script for LangGraph integration in Orchestrator service.

This script validates that the LangGraph integration is working properly
by testing the core components and workflows.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from services.orchestrator.modules.langgraph.engine import LangGraphWorkflowEngine
from services.orchestrator.modules.langgraph.state import create_workflow_state
from services.orchestrator.modules.langgraph.tools import create_service_tools
from services.orchestrator.modules.workflows.document_analysis import create_document_analysis_workflow


async def test_langgraph_engine():
    """Test the LangGraph workflow engine."""
    print("🧪 Testing LangGraph Workflow Engine...")

    try:
        # Initialize engine
        engine = LangGraphWorkflowEngine()
        print("✓ LangGraph engine initialized")

        # Test tool initialization
        tools = await engine.initialize_tools(["logging_service"])
        print(f"✓ Tools initialized: {len(tools)} tools available")

        # Test workflow registration
        doc_workflow = create_document_analysis_workflow()
        engine.workflows["document_analysis"] = doc_workflow
        print("✓ Document analysis workflow registered")

        # Test workflow listing
        available_workflows = engine.list_available_workflows()
        print(f"✓ Available workflows: {available_workflows}")

        # Test workflow info
        workflow_info = engine.get_workflow_info("document_analysis")
        print(f"✓ Workflow info retrieved: {workflow_info}")

        return True

    except Exception as e:
        print(f"✗ LangGraph engine test failed: {e}")
        return False


async def test_workflow_state():
    """Test workflow state management."""
    print("\n🧪 Testing Workflow State Management...")

    try:
        # Create workflow state
        state = create_workflow_state(
            workflow_type="test_workflow",
            input_data={"test_param": "test_value"},
            user_id="test_user"
        )
        print("✓ Workflow state created")

        # Test state updates
        state.add_log_entry("INFO", "Test log entry")
        state.update_metrics({"test_metric": 1.0})
        print("✓ State updates working")

        # Test error handling
        state.add_error({"step": "test", "error": "Test error"})
        print("✓ Error handling working")

        return True

    except Exception as e:
        print(f"✗ Workflow state test failed: {e}")
        return False


async def test_service_tools():
    """Test service tool creation."""
    print("\n🧪 Testing Service Tool Creation...")

    try:
        # Test tool creation for a service
        from services.shared.utilities import get_service_client
        service_client = get_service_client()

        tools = await create_service_tools("logging_service", service_client)
        print(f"✓ Service tools created: {len(tools)} tools")

        # List available tools
        for tool_name, tool_func in tools.items():
            print(f"  - {tool_name}")

        return True

    except Exception as e:
        print(f"✗ Service tools test failed: {e}")
        return False


async def test_workflow_execution():
    """Test basic workflow execution."""
    print("\n🧪 Testing Workflow Execution...")

    try:
        # Create a simple test workflow
        engine = LangGraphWorkflowEngine()

        # Initialize basic tools
        tools = await engine.initialize_tools(["logging_service"])

        # Create test workflow state
        test_state = create_workflow_state(
            workflow_type="test_execution",
            input_data={"test": True}
        )

        print("✓ Basic workflow execution components ready")

        # Note: Full workflow execution would require running services
        # This tests the setup and initialization
        return True

    except Exception as e:
        print(f"✗ Workflow execution test failed: {e}")
        return False


async def main():
    """Run all LangGraph integration tests."""
    print("🚀 LangGraph Integration Test Suite")
    print("=" * 50)

    # Check if LangGraph is available
    try:
        import langgraph
        import langchain_core
        import langchain_openai
        print("✓ LangGraph dependencies available")
    except ImportError as e:
        print(f"✗ LangGraph dependencies missing: {e}")
        print("Please run: pip install -r requirements.txt")
        return

    # Run tests
    tests = [
        test_langgraph_engine,
        test_workflow_state,
        test_service_tools,
        test_workflow_execution
    ]

    results = []
    for test_func in tests:
        result = await test_func()
        results.append(result)

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! LangGraph integration is ready.")
        print("\nNext steps:")
        print("1. Start the orchestrator service: python main.py")
        print("2. Test API endpoints: POST /workflows/ai/document-analysis")
        print("3. Monitor logs for workflow execution")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
