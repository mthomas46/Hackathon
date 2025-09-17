#!/usr/bin/env python3
"""
Workflow Management Demo Script

Demonstrates the workflow management infrastructure capabilities
without complex dependencies that can cause validation issues.
"""

import asyncio
import json
import sys
import os
import time

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))

# Import workflow management components
from services.orchestrator.modules.workflow_management.service import WorkflowManagementService
from services.orchestrator.modules.workflow_management.models import (
    WorkflowParameter, WorkflowAction, ParameterType, ActionType,
    WorkflowStatus, WorkflowExecutionStatus
)


async def demo_workflow_management():
    """Demonstrate workflow management capabilities."""
    print("🎯 WORKFLOW MANAGEMENT INFRASTRUCTURE DEMO")
    print("=" * 80)
    print("Demonstrating workflow creation, execution, and management...")
    print()

    # Initialize service
    workflow_service = WorkflowManagementService()

    # Demo 1: Create a simple workflow
    print("📝 DEMO 1: Creating a simple workflow...")
    try:
        workflow_data = {
            "name": "Simple Notification Workflow",
            "description": "A simple workflow that sends notifications",
            "tags": ["demo", "notification", "simple"],
            "parameters": [
                {
                    "name": "message",
                    "type": "string",
                    "description": "Message to send",
                    "required": True
                },
                {
                    "name": "priority",
                    "type": "string",
                    "description": "Notification priority",
                    "required": False,
                    "default_value": "normal",
                    "allowed_values": ["low", "normal", "high"]
                }
            ],
            "actions": [
                {
                    "action_type": "notification",
                    "name": "Send Notification",
                    "description": "Send the notification message",
                    "config": {
                        "message": "{{message}}",
                        "channels": ["console"],
                        "priority": "{{priority}}"
                    }
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(workflow_data, "demo_user")

        if success:
            print("✅ Simple workflow created successfully!")
            print(f"   • Workflow ID: {workflow.workflow_id}")
            print(f"   • Name: {workflow.name}")
            print(f"   • Parameters: {len(workflow.parameters)}")
            print(f"   • Actions: {len(workflow.actions)}")
            workflow_id = workflow.workflow_id
        else:
            print(f"❌ Workflow creation failed: {message}")
            return

    except Exception as e:
        print(f"❌ Demo 1 failed: {e}")
        return

    print()

    # Demo 2: Execute the workflow
    print("🚀 DEMO 2: Executing the workflow...")
    try:
        execution_params = {
            "message": "Hello from Workflow Management Demo!",
            "priority": "high"
        }

        success, message, execution = await workflow_service.execute_workflow(
            workflow_id, execution_params, "demo_user"
        )

        if success:
            print("✅ Workflow execution started successfully!")
            print(f"   • Execution ID: {execution.execution_id}")
            print(f"   • Status: {execution.status.value}")
            print(f"   • Parameters: {execution.input_parameters}")

            # Wait a moment for execution
            await asyncio.sleep(2)

            # Check execution status
            updated_execution = await workflow_service.get_execution(execution.execution_id)
            if updated_execution:
                print(f"   • Final Status: {updated_execution.status.value}")
                print(f"   • Execution Time: {updated_execution.execution_time_seconds:.2f}s")
                if updated_execution.output_data:
                    print(f"   • Output: {updated_execution.output_data}")

        else:
            print(f"❌ Workflow execution failed: {message}")

    except Exception as e:
        print(f"❌ Demo 2 failed: {e}")

    print()

    # Demo 3: List and search workflows
    print("📋 DEMO 3: Listing and searching workflows...")
    try:
        workflows = await workflow_service.list_workflows()

        print(f"✅ Found {len(workflows)} workflows")
        for wf in workflows:
            print(f"   • {wf.name} ({wf.workflow_id[:8]}...) - {wf.status.value}")

        # Search workflows
        search_results = await workflow_service.search_workflows("notification")
        print(f"   • Search results for 'notification': {len(search_results)} workflows")

    except Exception as e:
        print(f"❌ Demo 3 failed: {e}")

    print()

    # Demo 4: Get workflow statistics
    print("📊 DEMO 4: Workflow statistics...")
    try:
        stats = workflow_service.get_workflow_statistics()

        print("✅ Workflow Statistics:")
        print(f"   • Total Workflows: {stats.get('workflows', {}).get('total_workflows', 0)}")
        print(f"   • Active Workflows: {stats.get('workflows', {}).get('active_workflows', 0)}")
        print(f"   • Total Executions: {stats.get('executions', {}).get('total_executions', 0)}")
        print(f"   • Success Rate: {stats.get('executions', {}).get('total_executions', 0) and (stats.get('executions', {}).get('completed_executions', 0) / stats.get('executions', {}).get('total_executions', 0) * 100):.1f}%")

    except Exception as e:
        print(f"❌ Demo 4 failed: {e}")

    print()

    # Demo 5: Update workflow
    print("✏️  DEMO 5: Updating workflow...")
    try:
        updates = {
            "description": "Updated demo workflow with enhanced description",
            "tags": ["demo", "notification", "simple", "updated"]
        }

        success, message = await workflow_service.update_workflow(workflow_id, updates, "demo_user")

        if success:
            print("✅ Workflow updated successfully!")
            print(f"   • Message: {message}")

            # Verify update
            updated_workflow = await workflow_service.get_workflow(workflow_id)
            if updated_workflow and "updated" in updated_workflow.tags:
                print("   • Verification: Tags updated successfully")
        else:
            print(f"❌ Workflow update failed: {message}")

    except Exception as e:
        print(f"❌ Demo 5 failed: {e}")

    print()
    print("🎯 WORKFLOW MANAGEMENT API ENDPOINTS")
    print("=" * 80)
    print("The following REST API endpoints are now available:")
    print()
    print("📝 Workflow Management:")
    print("   POST   /workflows                     - Create new workflow")
    print("   GET    /workflows                     - List workflows (with filtering)")
    print("   GET    /workflows/search              - Search workflows")
    print("   GET    /workflows/{id}                - Get specific workflow")
    print("   PUT    /workflows/{id}                - Update workflow")
    print("   DELETE /workflows/{id}                - Delete workflow")
    print()
    print("🚀 Workflow Execution:")
    print("   POST   /workflows/{id}/execute        - Execute workflow")
    print("   GET    /workflows/executions/{id}     - Get execution details")
    print("   GET    /workflows/{id}/executions     - List workflow executions")
    print("   POST   /workflows/executions/{id}/cancel - Cancel execution")
    print()
    print("🎯 Advanced Features:")
    print("   POST   /workflows/from-template       - Create from template")
    print("   GET    /workflows/templates           - List available templates")
    print("   GET    /workflows/templates/{name}    - Get template details")
    print("   GET    /workflows/statistics          - Get workflow statistics")
    print("   GET    /workflows/activity            - Get recent activity")
    print("   GET    /workflows/health              - Health check")
    print()
    print("📋 Usage Examples:")
    print()
    print("1. Create a workflow:")
    print('   POST /workflows')
    print('   {')
    print('     "name": "My Workflow",')
    print('     "description": "Workflow description",')
    print('     "parameters": [')
    print('       {"name": "input", "type": "string", "required": true}')
    print('     ],')
    print('     "actions": [')
    print('       {"action_type": "notification", "name": "Notify", "config": {"message": "Hello"}}')
    print('     ]')
    print('   }')
    print()
    print("2. Execute a workflow:")
    print('   POST /workflows/{workflow_id}/execute')
    print('   {"parameters": {"input": "test value"}}')
    print()
    print("3. List workflows with filtering:")
    print('   GET /workflows?status=active&created_by=user&name_contains=document')
    print()
    print("🎉 WORKFLOW MANAGEMENT INFRASTRUCTURE READY!")
    print("   • Create parameterized workflows via API")
    print("   • Execute complex multi-step processes")
    print("   • Monitor and manage workflow lifecycle")
    print("   • Real-time execution tracking and statistics")
    print("   • Template-based workflow creation")
    print()
    print("=" * 80)
    print("🏁 Workflow Management Demo Complete")
    print("=" * 80)


async def demo_api_usage():
    """Demonstrate API usage patterns."""
    print("🔧 API USAGE PATTERNS")
    print("=" * 50)

    print("1. Creating a parameterized workflow:")
    print("""
    curl -X POST http://localhost:5080/workflows \\
         -H "Content-Type: application/json" \\
         -d '{
           "name": "Document Processor",
           "description": "Process documents with analysis",
           "parameters": [
             {
               "name": "document_url",
               "type": "string",
               "description": "URL of document to process",
               "required": true
             },
             {
               "name": "analysis_type",
               "type": "string",
               "allowed_values": ["quality", "consistency", "sentiment"],
               "default_value": "quality"
             }
           ],
           "actions": [
             {
               "action_type": "service_call",
               "name": "Fetch Document",
               "config": {
                 "service": "source_agent",
                 "endpoint": "/fetch",
                 "method": "POST",
                 "parameters": {"url": "{{document_url}}"}
               }
             },
             {
               "action_type": "service_call",
               "name": "Analyze",
               "config": {
                 "service": "analysis_service",
                 "endpoint": "/analyze",
                 "parameters": {"type": "{{analysis_type}}"}
               }
             }
           ]
         }'
    """)

    print("2. Executing the workflow:")
    print("""
    curl -X POST http://localhost:5080/workflows/{workflow_id}/execute \\
         -H "Content-Type: application/json" \\
         -d '{
           "parameters": {
             "document_url": "https://example.com/doc.pdf",
             "analysis_type": "quality"
           }
         }'
    """)

    print("3. Monitoring execution:")
    print("""
    curl http://localhost:5080/workflows/executions/{execution_id}
    """)

    print("4. Listing workflows:")
    print("""
    curl "http://localhost:5080/workflows?status=active&limit=10"
    """)


if __name__ == "__main__":
    async def main():
        # Run main demo
        await demo_workflow_management()

        print()

        # Show API usage patterns
        await demo_api_usage()

    asyncio.run(main())
