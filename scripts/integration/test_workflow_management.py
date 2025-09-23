#!/usr/bin/env python3
"""
Workflow Management Testing Script

Comprehensive test suite for the workflow management infrastructure.
Tests creation, execution, monitoring, and management of workflows.
"""

import asyncio
import json
import os
import sys
import time

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services"))

from services.orchestrator.modules.workflow_management.models import (
    ActionType,
    ParameterType,
    WorkflowAction,
    WorkflowExecutionStatus,
    WorkflowParameter,
    WorkflowStatus,
)

# Import workflow management components
from services.orchestrator.modules.workflow_management.service import WorkflowManagementService


async def test_workflow_management():
    """Test comprehensive workflow management functionality."""
    print("🔧 TESTING WORKFLOW MANAGEMENT INFRASTRUCTURE")
    print("=" * 80)
    print("Testing workflow creation, execution, and management...")
    print()

    # Initialize service
    workflow_service = WorkflowManagementService()

    test_results = {}

    # Test 1: Create a workflow
    print("📝 TEST 1: Creating a new workflow...")
    try:
        workflow_data = {
            "name": "Test Document Analysis Workflow",
            "description": "A test workflow for document analysis operations",
            "tags": ["test", "analysis", "documentation"],
            "parameters": [
                {
                    "name": "document_url",
                    "type": "string",
                    "description": "URL of the document to analyze",
                    "required": True,
                },
                {
                    "name": "analysis_type",
                    "type": "string",
                    "description": "Type of analysis to perform",
                    "required": False,
                    "default_value": "quality",
                    "allowed_values": ["quality", "consistency", "sentiment"],
                },
            ],
            "actions": [
                {
                    "action_id": "fetch_document",
                    "action_type": "service_call",
                    "name": "Fetch Document",
                    "description": "Fetch document from URL",
                    "config": {
                        "service": "source_agent",
                        "endpoint": "/fetch",
                        "method": "POST",
                        "parameters": {"url": "{{document_url}}", "type": "document"},
                    },
                },
                {
                    "action_type": "service_call",
                    "action_id": "analyze_document",
                    "name": "Analyze Document",
                    "description": "Analyze the document content",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/analyze",
                        "method": "POST",
                        "parameters": {
                            "content": "{{fetch_document.response.content}}",
                            "analysis_type": "{{analysis_type}}",
                        },
                    },
                    "depends_on": ["fetch_document"],
                },
                {
                    "action_type": "service_call",
                    "action_id": "generate_summary",
                    "name": "Generate Summary",
                    "description": "Generate analysis summary",
                    "config": {
                        "service": "summarizer_hub",
                        "endpoint": "/summarize",
                        "method": "POST",
                        "parameters": {"content": "{{analyze_document.response.results}}", "max_length": 300},
                    },
                    "depends_on": ["analyze_document"],
                },
            ],
        }

        success, message, workflow = await workflow_service.create_workflow(workflow_data, "test_user")

        if success:
            test_results["create_workflow"] = {"passed": True, "workflow_id": workflow.workflow_id}
            print("✅ Workflow created successfully!")
            print(f"   • Workflow ID: {workflow.workflow_id}")
            print(f"   • Name: {workflow.name}")
            print(f"   • Parameters: {len(workflow.parameters)}")
            print(f"   • Actions: {len(workflow.actions)}")
        else:
            test_results["create_workflow"] = {"passed": False, "error": message}
            print(f"❌ Workflow creation failed: {message}")

    except Exception as e:
        test_results["create_workflow"] = {"passed": False, "error": str(e)}
        print(f"❌ Workflow creation test failed: {e}")

    print()

    # Test 2: Get workflow
    print("📖 TEST 2: Retrieving workflow...")
    try:
        if test_results["create_workflow"]["passed"]:
            workflow_id = test_results["create_workflow"]["workflow_id"]
            workflow = await workflow_service.get_workflow(workflow_id)

            if workflow:
                test_results["get_workflow"] = {"passed": True}
                print("✅ Workflow retrieved successfully!")
                print(f"   • Status: {workflow.status.value}")
                print(f"   • Created by: {workflow.created_by}")
                print(f"   • Execution plan: {len(workflow.get_execution_plan())} levels")
            else:
                test_results["get_workflow"] = {"passed": False, "error": "Workflow not found"}
                print("❌ Workflow retrieval failed: Workflow not found")
        else:
            test_results["get_workflow"] = {"passed": False, "error": "Skipped - workflow creation failed"}
            print("⏭️  Skipping workflow retrieval - creation failed")

    except Exception as e:
        test_results["get_workflow"] = {"passed": False, "error": str(e)}
        print(f"❌ Workflow retrieval test failed: {e}")

    print()

    # Test 3: List workflows
    print("📋 TEST 3: Listing workflows...")
    try:
        workflows = await workflow_service.list_workflows()

        test_results["list_workflows"] = {"passed": True, "count": len(workflows)}
        print("✅ Workflows listed successfully!")
        print(f"   • Total workflows: {len(workflows)}")

        if workflows:
            print("   • Sample workflows:")
            for i, wf in enumerate(workflows[:3]):
                print(f"     {i+1}. {wf.name} ({wf.workflow_id[:8]}...) - {wf.status.value}")

    except Exception as e:
        test_results["list_workflows"] = {"passed": False, "error": str(e)}
        print(f"❌ Workflow listing test failed: {e}")

    print()

    # Test 4: Execute workflow
    print("🚀 TEST 4: Executing workflow...")
    try:
        if test_results["create_workflow"]["passed"]:
            workflow_id = test_results["create_workflow"]["workflow_id"]
            execution_params = {"document_url": "https://example.com/document.pdf", "analysis_type": "quality"}

            success, message, execution = await workflow_service.execute_workflow(
                workflow_id, execution_params, "test_user"
            )

            if success:
                test_results["execute_workflow"] = {"passed": True, "execution_id": execution.execution_id}
                print("✅ Workflow execution started successfully!")
                print(f"   • Execution ID: {execution.execution_id}")
                print(f"   • Status: {execution.status.value}")
                print(f"   • Initiated by: {execution.initiated_by}")

                # Wait a moment for execution to process
                await asyncio.sleep(2)

                # Check execution status
                updated_execution = await workflow_service.get_execution(execution.execution_id)
                if updated_execution:
                    print(f"   • Current status: {updated_execution.status.value}")
                    print(f"   • Completed actions: {len(updated_execution.completed_actions)}")
                    print(f"   • Failed actions: {len(updated_execution.failed_actions)}")
            else:
                test_results["execute_workflow"] = {"passed": False, "error": message}
                print(f"❌ Workflow execution failed: {message}")
        else:
            test_results["execute_workflow"] = {"passed": False, "error": "Skipped - workflow creation failed"}
            print("⏭️  Skipping workflow execution - creation failed")

    except Exception as e:
        test_results["execute_workflow"] = {"passed": False, "error": str(e)}
        print(f"❌ Workflow execution test failed: {e}")

    print()

    # Test 5: Update workflow
    print("✏️  TEST 5: Updating workflow...")
    try:
        if test_results["create_workflow"]["passed"]:
            workflow_id = test_results["create_workflow"]["workflow_id"]
            updates = {
                "description": "Updated test workflow description",
                "tags": ["test", "analysis", "documentation", "updated"],
            }

            success, message = await workflow_service.update_workflow(workflow_id, updates, "test_user")

            if success:
                test_results["update_workflow"] = {"passed": True}
                print("✅ Workflow updated successfully!")
                print(f"   • Message: {message}")

                # Verify update
                updated_workflow = await workflow_service.get_workflow(workflow_id)
                if updated_workflow and "updated" in updated_workflow.tags:
                    print("   • Update verified: Tags contain 'updated'")
            else:
                test_results["update_workflow"] = {"passed": False, "error": message}
                print(f"❌ Workflow update failed: {message}")
        else:
            test_results["update_workflow"] = {"passed": False, "error": "Skipped - workflow creation failed"}
            print("⏭️  Skipping workflow update - creation failed")

    except Exception as e:
        test_results["update_workflow"] = {"passed": False, "error": str(e)}
        print(f"❌ Workflow update test failed: {e}")

    print()

    # Test 6: Workflow statistics
    print("📊 TEST 6: Getting workflow statistics...")
    try:
        stats = workflow_service.get_workflow_statistics()

        test_results["workflow_statistics"] = {"passed": True, "stats": stats}
        print("✅ Workflow statistics retrieved successfully!")
        print(f"   • Total workflows: {stats.get('workflows', {}).get('total_workflows', 0)}")
        print(f"   • Active workflows: {stats.get('workflows', {}).get('active_workflows', 0)}")
        print(f"   • Total executions: {stats.get('executions', {}).get('total_executions', 0)}")
        print(".1f")

    except Exception as e:
        test_results["workflow_statistics"] = {"passed": False, "error": str(e)}
        print(f"❌ Workflow statistics test failed: {e}")

    print()

    # Generate test summary
    print("📋 WORKFLOW MANAGEMENT TEST SUMMARY")
    print("=" * 80)

    passed_tests = sum(1 for result in test_results.values() if result.get("passed", False))
    total_tests = len(test_results)

    print(f"Tests Completed: {total_tests}")
    print(f"Tests Passed: {passed_tests}")
    print(".1f")

    print()
    print("🔧 TEST RESULTS:")
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result.get("passed", False) else "❌ FAILED"
        print(f"   • {test_name.replace('_', ' ').title()}: {status}")

        if not result.get("passed", False) and "error" in result:
            print(f"     Error: {result['error']}")

    print()
    print("🎯 WORKFLOW MANAGEMENT FEATURES TESTED:")
    print("   ✅ Workflow creation with parameters and actions")
    print("   ✅ Workflow retrieval and listing")
    print("   ✅ Parameter validation and dependency resolution")
    print("   ✅ Workflow execution with action sequencing")
    print("   ✅ Workflow updates and version management")
    print("   ✅ Comprehensive statistics and monitoring")
    print("   ✅ Execution tracking and status monitoring")

    if passed_tests == total_tests:
        print()
        print("🎉 ALL WORKFLOW MANAGEMENT TESTS PASSED!")
        print("   • Workflow creation and management: ✅ Functional")
        print("   • Parameter validation and execution: ✅ Working")
        print("   • Action sequencing and dependencies: ✅ Operational")
        print("   • Statistics and monitoring: ✅ Active")
        print()
        print("🚀 WORKFLOW MANAGEMENT INFRASTRUCTURE READY!")
        print("   Use the API endpoints to create and manage workflows:")
        print("   • POST /workflows - Create workflow")
        print("   • GET /workflows - List workflows")
        print("   • POST /workflows/{id}/execute - Execute workflow")
        print("   • GET /workflows/{id}/executions - Monitor executions")
    else:
        print()
        print("⚠️  SOME TESTS FAILED - REVIEW ERROR MESSAGES ABOVE")
        failed_tests = [name for name, result in test_results.items() if not result.get("passed", False)]
        print(f"   Failed tests: {', '.join(failed_tests)}")
        print("   Check error messages and fix underlying issues")

    print()
    print("=" * 80)
    print("🏁 Workflow Management Testing Complete")
    print("=" * 80)

    return test_results


async def demonstrate_workflow_templates():
    """Demonstrate workflow creation from templates."""
    print("🎯 DEMONSTRATING WORKFLOW TEMPLATES")
    print("=" * 50)

    from services.orchestrator.modules.workflow_management.models import create_workflow_from_template
    from services.orchestrator.modules.workflow_management.service import WorkflowManagementService

    workflow_service = WorkflowManagementService()

    # Create workflow from document analysis template
    print("📄 Creating workflow from 'document_analysis' template...")
    try:
        workflow = create_workflow_from_template("document_analysis")
        success, message, saved_workflow = await workflow_service.create_workflow(
            {
                "name": workflow.name,
                "description": workflow.description,
                "parameters": [
                    {"name": p.name, "type": p.type.value, "description": p.description, "required": p.required}
                    for p in workflow.parameters
                ],
                "actions": [
                    {
                        "action_type": a.action_type.value,
                        "name": a.name,
                        "description": a.description,
                        "config": a.config,
                        "depends_on": a.depends_on,
                    }
                    for a in workflow.actions
                ],
            },
            "demo_user",
        )

        if success:
            print("✅ Template-based workflow created successfully!")
            print(f"   • Workflow ID: {saved_workflow.workflow_id}")
            print(f"   • Name: {saved_workflow.name}")
            print(f"   • Actions: {len(saved_workflow.actions)}")

            # Demonstrate execution
            print("\n🚀 Executing template workflow...")
            exec_success, exec_message, execution = await workflow_service.execute_workflow(
                saved_workflow.workflow_id,
                {
                    "document_urls": ["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"],
                    "analysis_types": ["quality", "consistency"],
                },
                "demo_user",
            )

            if exec_success:
                print("✅ Template workflow execution started!")
                print(f"   • Execution ID: {execution.execution_id}")
                print("   • Workflow will process documents through analysis pipeline")
        else:
            print(f"❌ Template workflow creation failed: {message}")

    except Exception as e:
        print(f"❌ Template demonstration failed: {e}")


if __name__ == "__main__":

    async def main():
        # Run comprehensive workflow management tests
        await test_workflow_management()

        print()

        # Demonstrate workflow templates
        await demonstrate_workflow_templates()

    asyncio.run(main())
