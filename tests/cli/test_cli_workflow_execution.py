"""
CLI Workflow Execution End-to-End Tests

Comprehensive end-to-end tests for CLI workflow execution scenarios including:
- Complete workflow lifecycle from creation to execution
- Multi-service workflow orchestration
- Real-time execution monitoring
- Workflow status tracking and management
- Error handling and recovery scenarios
- Performance monitoring of workflow execution
"""

import sys
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from io import StringIO
import json
import time
import uuid

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from ecosystem_cli_executable import EcosystemCLI
from .mock_framework import CLIMockFramework, create_successful_service_test
from .test_fixtures import CLITestFixtures


class TestCLIWorkflowExecution:
    """End-to-end tests for CLI workflow execution scenarios"""

    def setup_method(self):
        """Setup test method"""
        self.cli = EcosystemCLI()
        self.fixtures = CLITestFixtures()
        self.mock_framework = CLIMockFramework()

    @pytest.mark.asyncio
    async def test_complete_workflow_lifecycle(self):
        """Test complete workflow lifecycle from creation to completion"""
        with self.mock_framework.mock_cli_environment():
            # Setup orchestrator responses for complete workflow lifecycle
            workflow_id = str(uuid.uuid4())

            # Step 1: Create workflow response
            create_response = {
                "workflow_id": workflow_id,
                "name": "test-workflow",
                "status": "created",
                "created_at": "2024-01-20T10:00:00Z",
                "steps": [
                    {"name": "data-collection", "service": "doc_store"},
                    {"name": "analysis", "service": "analysis-service"},
                    {"name": "reporting", "service": "summarizer-hub"}
                ]
            }
            from .test_fixtures import MockServiceResponse
            create_workflow_response = MockServiceResponse(status_code=201, json_data=create_response)
            self.mock_framework.http_client.add_response("orchestrator_create_workflow", create_workflow_response)

            # Step 2: Execute workflow response
            execution_id = str(uuid.uuid4())
            execute_response = {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": "running",
                "started_at": "2024-01-20T10:00:05Z",
                "message": "Workflow execution started successfully"
            }
            execute_workflow_response = MockServiceResponse(status_code=202, json_data=execute_response)
            self.mock_framework.http_client.add_response("orchestrator_execute_workflow", execute_workflow_response)

            # Step 3: Status check responses (multiple calls)
            status_responses = [
                {
                    "id": execution_id,
                    "workflow_name": "test-workflow",
                    "status": "running",
                    "progress": 25,
                    "started_at": "2024-01-20T10:00:05Z",
                    "current_step": "data-collection",
                    "steps": [
                        {"name": "data-collection", "status": "completed", "duration": 15},
                        {"name": "analysis", "status": "running", "duration": None},
                        {"name": "reporting", "status": "pending", "duration": None}
                    ]
                },
                {
                    "id": execution_id,
                    "workflow_name": "test-workflow",
                    "status": "running",
                    "progress": 75,
                    "started_at": "2024-01-20T10:00:05Z",
                    "current_step": "reporting",
                    "steps": [
                        {"name": "data-collection", "status": "completed", "duration": 15},
                        {"name": "analysis", "status": "completed", "duration": 45},
                        {"name": "reporting", "status": "running", "duration": None}
                    ]
                },
                {
                    "id": execution_id,
                    "workflow_name": "test-workflow",
                    "status": "completed",
                    "progress": 100,
                    "started_at": "2024-01-20T10:00:05Z",
                    "completed_at": "2024-01-20T10:02:30Z",
                    "total_duration": 145,
                    "steps": [
                        {"name": "data-collection", "status": "completed", "duration": 15},
                        {"name": "analysis", "status": "completed", "duration": 45},
                        {"name": "reporting", "status": "completed", "duration": 85}
                    ],
                    "results": {
                        "documents_processed": 25,
                        "analysis_reports": 5,
                        "summary_generated": True
                    }
                }
            ]

            # Add status responses with different keys for different calls
            for i, status_data in enumerate(status_responses):
                status_response = MockServiceResponse(status_code=200, json_data=status_data)
                self.mock_framework.http_client.add_response(f"orchestrator_execution_status_{i}", status_response)

            # Step 4: List executions response
            executions_list = [
                {
                    "id": execution_id,
                    "workflow_name": "test-workflow",
                    "status": "completed",
                    "started_at": "2024-01-20T10:00:05Z",
                    "completed_at": "2024-01-20T10:02:30Z",
                    "duration": 145
                }
            ]
            list_executions_response = MockServiceResponse(status_code=200, json_data={"items": executions_list, "total": 1})
            self.mock_framework.http_client.add_response("orchestrator_list_executions", list_executions_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Execute complete workflow lifecycle

                # 1. Create workflow
                await self.cli.orchestrator_command("create-workflow", type="mock-data")

                # 2. Execute workflow
                await self.cli.orchestrator_command("execute", id=workflow_id)

                # 3. Check status multiple times (simulating monitoring)
                await self.cli.orchestrator_command("execution-status", id=execution_id)

                # 4. List executions
                await self.cli.orchestrator_command("list-executions")

                output = mock_stdout.getvalue()

                # Verify complete workflow lifecycle
                assert "🔄 Orchestrator: Creating mock data workflow..." in output
                assert "🚀 Workflow Execution Started:" in output
                assert "📊 Execution Status:" in output
                assert "📋 Workflow Executions" in output
                assert workflow_id[:8] in output  # Partial workflow ID
                assert execution_id[:8] in output  # Partial execution ID
                assert "completed" in output
                assert "100" in output  # Progress percentage

    @pytest.mark.asyncio
    async def test_workflow_execution_with_error_recovery(self):
        """Test workflow execution with error handling and recovery"""
        with self.mock_framework.mock_cli_environment():
            workflow_id = str(uuid.uuid4())
            execution_id = str(uuid.uuid4())

            # Setup initial workflow creation
            create_response = {
                "workflow_id": workflow_id,
                "name": "error-recovery-workflow",
                "status": "created"
            }
            from .test_fixtures import MockServiceResponse
            create_workflow_response = MockServiceResponse(status_code=201, json_data=create_response)
            self.mock_framework.http_client.add_response("orchestrator_create_workflow", create_workflow_response)

            # Setup execution that initially fails
            failed_execution_response = MockServiceResponse(
                status_code=200,
                json_data={
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": "Service temporarily unavailable",
                    "failed_step": "data-collection",
                    "can_retry": True
                }
            )
            self.mock_framework.http_client.add_response("orchestrator_execute_failed", failed_execution_response)

            # Setup successful retry
            retry_execution_response = MockServiceResponse(
                status_code=200,
                json_data={
                    "execution_id": execution_id + "_retry",
                    "status": "running",
                    "message": "Workflow retry initiated"
                }
            )
            self.mock_framework.http_client.add_response("orchestrator_execute_retry", retry_execution_response)

            # Setup recovery status
            recovery_status_response = MockServiceResponse(
                status_code=200,
                json_data={
                    "id": execution_id + "_retry",
                    "status": "completed",
                    "recovery_attempt": True,
                    "original_execution": execution_id
                }
            )
            self.mock_framework.http_client.add_response("orchestrator_recovery_status", recovery_status_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Execute workflow with error recovery
                await self.cli.orchestrator_command("create-workflow", type="mock-data")
                await self.cli.orchestrator_command("execute", id=workflow_id)

                # Simulate retry after failure
                await self.cli.orchestrator_command("execute", id=workflow_id)
                await self.cli.orchestrator_command("execution-status", id=execution_id + "_retry")

                output = mock_stdout.getvalue()

                # Verify error recovery workflow
                assert "failed" in output
                assert "Service temporarily unavailable" in output
                assert "Workflow retry initiated" in output
                assert "recovery_attempt" in output

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self):
        """Test concurrent execution of multiple workflows"""
        with self.mock_framework.mock_cli_environment():
            # Setup multiple concurrent workflows
            workflow_ids = [str(uuid.uuid4()) for _ in range(3)]
            execution_ids = [str(uuid.uuid4()) for _ in range(3)]

            # Setup creation responses
            for i, workflow_id in enumerate(workflow_ids):
                create_response = {
                    "workflow_id": workflow_id,
                    "name": f"concurrent-workflow-{i+1}",
                    "status": "created"
                }
                from .test_fixtures import MockServiceResponse
                response = MockServiceResponse(status_code=201, json_data=create_response)
                self.mock_framework.http_client.add_response(f"orchestrator_create_{i}", response)

            # Setup execution responses
            for i, (workflow_id, execution_id) in enumerate(zip(workflow_ids, execution_ids)):
                execute_response = {
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                    "status": "running",
                    "concurrent_execution": True
                }
                response = MockServiceResponse(status_code=202, json_data=execute_response)
                self.mock_framework.http_client.add_response(f"orchestrator_execute_{i}", response)

            # Setup status responses showing different progress levels
            for i, execution_id in enumerate(execution_ids):
                progress = (i + 1) * 30  # 30%, 60%, 90%
                status_response = {
                    "id": execution_id,
                    "status": "running",
                    "progress": progress,
                    "concurrent_batch": f"batch_{i+1}"
                }
                response = MockServiceResponse(status_code=200, json_data=status_response)
                self.mock_framework.http_client.add_response(f"orchestrator_status_{i}", response)

            # Execute concurrent workflows
            tasks = []
            for i, workflow_id in enumerate(workflow_ids):
                task = asyncio.create_task(self.execute_single_workflow(workflow_id, execution_ids[i], i))
                tasks.append(task)

            # Wait for all workflows to complete
            await asyncio.gather(*tasks)

            # Verify concurrent execution results
            # (In a real test, we'd capture and verify the output from each task)

    async def execute_single_workflow(self, workflow_id: str, execution_id: str, index: int):
        """Helper method to execute a single workflow"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # Create workflow
            await self.cli.orchestrator_command("create-workflow", type="mock-data")

            # Execute workflow
            await self.cli.orchestrator_command("execute", id=workflow_id)

            # Check status
            await self.cli.orchestrator_command("execution-status", id=execution_id)

            return mock_stdout.getvalue()

    @pytest.mark.asyncio
    async def test_workflow_template_usage(self):
        """Test workflow template creation and usage"""
        with self.mock_framework.mock_cli_environment():
            # Setup template listing response
            templates_data = [
                {
                    "name": "document-analysis",
                    "description": "Analyze documents for insights and patterns",
                    "category": "analysis",
                    "parameters": ["input_documents", "analysis_type"]
                },
                {
                    "name": "data-processing",
                    "description": "Process and transform data",
                    "category": "processing",
                    "parameters": ["input_data", "transformations"]
                },
                {
                    "name": "report-generation",
                    "description": "Generate comprehensive reports",
                    "category": "reporting",
                    "parameters": ["data_sources", "report_format"]
                }
            ]
            from .test_fixtures import MockServiceResponse
            templates_response = MockServiceResponse(status_code=200, json_data=templates_data)
            self.mock_framework.http_client.add_response("orchestrator_templates", templates_response)

            # Setup template creation response
            template_create_response = {
                "workflow_id": str(uuid.uuid4()),
                "name": "my-document-analysis",
                "template": "document-analysis",
                "parameters": {"analysis_type": "comprehensive"},
                "status": "created"
            }
            create_from_template_response = MockServiceResponse(status_code=201, json_data=template_create_response)
            self.mock_framework.http_client.add_response("orchestrator_create_from_template", create_from_template_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # List available templates
                await self.cli.orchestrator_command("workflow-templates")

                # Create workflow from template
                await self.cli.orchestrator_command("create-template",
                    template="document-analysis",
                    name="my-document-analysis",
                    parameters='{"analysis_type": "comprehensive"}'
                )

                output = mock_stdout.getvalue()

                # Verify template workflow
                assert "📋 Available Workflow Templates:" in output
                assert "document-analysis" in output
                assert "data-processing" in output
                assert "report-generation" in output
                assert "✅ Workflow Created from Template:" in output
                assert "my-document-analysis" in output

    @pytest.mark.asyncio
    async def test_workflow_execution_monitoring(self):
        """Test real-time workflow execution monitoring"""
        with self.mock_framework.mock_cli_environment():
            execution_id = str(uuid.uuid4())

            # Setup execution start
            start_response = {
                "execution_id": execution_id,
                "status": "running",
                "monitoring_enabled": True,
                "real_time_updates": True
            }
            from .test_fixtures import MockServiceResponse
            start_execution_response = MockServiceResponse(status_code=202, json_data=start_response)
            self.mock_framework.http_client.add_response("orchestrator_start_monitoring", start_execution_response)

            # Setup monitoring updates
            monitoring_updates = [
                {
                    "execution_id": execution_id,
                    "timestamp": "2024-01-20T10:00:10Z",
                    "step": "data-collection",
                    "progress": 15,
                    "status": "running",
                    "message": "Collecting source documents"
                },
                {
                    "execution_id": execution_id,
                    "timestamp": "2024-01-20T10:00:30Z",
                    "step": "analysis",
                    "progress": 45,
                    "status": "running",
                    "message": "Analyzing document patterns"
                },
                {
                    "execution_id": execution_id,
                    "timestamp": "2024-01-20T10:01:00Z",
                    "step": "reporting",
                    "progress": 80,
                    "status": "running",
                    "message": "Generating final report"
                },
                {
                    "execution_id": execution_id,
                    "timestamp": "2024-01-20T10:01:30Z",
                    "step": "reporting",
                    "progress": 100,
                    "status": "completed",
                    "message": "Workflow completed successfully"
                }
            ]

            # Add monitoring updates
            for i, update in enumerate(monitoring_updates):
                update_response = MockServiceResponse(status_code=200, json_data=update)
                self.mock_framework.http_client.add_response(f"orchestrator_monitoring_{i}", update_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Start monitored execution
                workflow_def = '{"name":"monitored-workflow","steps":[{"name":"data-collection","service":"doc_store"}]}'
                await self.cli.orchestrator_command("execute", definition=workflow_def)

                # Simulate monitoring calls
                for i in range(len(monitoring_updates)):
                    await self.cli.orchestrator_command("execution-status", id=execution_id)

                output = mock_stdout.getvalue()

                # Verify monitoring output
                assert "🚀 Workflow Execution Started:" in output
                assert "monitoring_enabled" in output
                assert "real_time_updates" in output
                assert "Collecting source documents" in output
                assert "Analyzing document patterns" in output
                assert "Generating final report" in output
                assert "Workflow completed successfully" in output

    @pytest.mark.asyncio
    async def test_workflow_cancellation_and_cleanup(self):
        """Test workflow cancellation and cleanup procedures"""
        with self.mock_framework.mock_cli_environment():
            execution_id = str(uuid.uuid4())

            # Setup running execution
            running_response = {
                "execution_id": execution_id,
                "status": "running",
                "progress": 50,
                "current_step": "data-processing"
            }
            from .test_fixtures import MockServiceResponse
            running_execution_response = MockServiceResponse(status_code=200, json_data=running_response)
            self.mock_framework.http_client.add_response("orchestrator_running", running_execution_response)

            # Setup cancellation response
            cancel_response = {
                "execution_id": execution_id,
                "status": "cancelling",
                "message": "Cancellation requested, cleaning up resources",
                "cleanup_steps": ["stop_current_step", "rollback_changes", "free_resources"]
            }
            cancel_execution_response = MockServiceResponse(status_code=200, json_data=cancel_response)
            self.mock_framework.http_client.add_response("orchestrator_cancel", cancel_execution_response)

            # Setup cancelled status
            cancelled_response = {
                "execution_id": execution_id,
                "status": "cancelled",
                "progress": 50,
                "cancelled_at": "2024-01-20T10:15:00Z",
                "cleanup_completed": True,
                "resources_freed": ["temporary_files", "database_connections"]
            }
            cancelled_status_response = MockServiceResponse(status_code=200, json_data=cancelled_response)
            self.mock_framework.http_client.add_response("orchestrator_cancelled_status", cancelled_status_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Check running execution
                await self.cli.orchestrator_command("execution-status", id=execution_id)

                # Cancel execution
                await self.cli.orchestrator_command("cancel-execution", id=execution_id)

                # Check cancelled status
                await self.cli.orchestrator_command("execution-status", id=execution_id)

                output = mock_stdout.getvalue()

                # Verify cancellation workflow
                assert "running" in output
                assert "data-processing" in output
                assert "✅ Execution" in output and "cancellation requested" in output
                assert "cancelling" in output
                assert "cleaning up resources" in output
                assert "cancelled" in output
                assert "cleanup_completed" in output

    @pytest.mark.asyncio
    async def test_workflow_performance_monitoring(self):
        """Test workflow performance monitoring and metrics"""
        with self.mock_framework.mock_cli_environment():
            execution_id = str(uuid.uuid4())

            # Setup performance metrics
            performance_data = {
                "execution_id": execution_id,
                "performance_metrics": {
                    "total_duration": 145.5,
                    "step_durations": {
                        "data-collection": 25.2,
                        "analysis": 67.8,
                        "reporting": 52.5
                    },
                    "resource_usage": {
                        "cpu_percent": 45.2,
                        "memory_mb": 256.8,
                        "network_io_mb": 12.3
                    },
                    "efficiency_metrics": {
                        "throughput": 5.2,  # items per second
                        "success_rate": 98.5,
                        "error_rate": 1.5
                    }
                },
                "bottlenecks": [
                    {
                        "step": "analysis",
                        "bottleneck_type": "cpu_intensive",
                        "duration_impact": 15.3
                    }
                ],
                "optimization_suggestions": [
                    "Consider parallel processing for analysis step",
                    "Implement caching for repeated data access",
                    "Optimize database queries in reporting step"
                ]
            }

            from .test_fixtures import MockServiceResponse
            performance_response = MockServiceResponse(status_code=200, json_data=performance_data)
            self.mock_framework.http_client.add_response("orchestrator_performance", performance_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Get execution status with performance metrics
                await self.cli.orchestrator_command("execution-status", id=execution_id)

                output = mock_stdout.getvalue()

                # Verify performance monitoring
                assert "📊 Execution Status:" in output
                assert "performance_metrics" in output
                assert "145.5" in output  # total duration
                assert "45.2" in output  # CPU usage
                assert "98.5" in output  # success rate
                assert "Consider parallel processing" in output

    @pytest.mark.asyncio
    async def test_workflow_definition_execution(self):
        """Test workflow execution from JSON definition"""
        with self.mock_framework.mock_cli_environment():
            # Create workflow definition
            workflow_definition = {
                "name": "custom-analysis-workflow",
                "description": "Custom workflow for document analysis",
                "steps": [
                    {
                        "name": "document-collection",
                        "service": "doc_store",
                        "action": "list",
                        "parameters": {"limit": 50}
                    },
                    {
                        "name": "content-analysis",
                        "service": "analysis-service",
                        "action": "analyze",
                        "parameters": {"analysis_type": "sentiment"}
                    },
                    {
                        "name": "report-generation",
                        "service": "summarizer-hub",
                        "action": "summarize",
                        "parameters": {"format": "markdown"}
                    }
                ],
                "error_handling": {
                    "retry_policy": {"max_attempts": 3, "backoff": "exponential"},
                    "failure_action": "rollback"
                }
            }

            # Setup execution response
            definition_execution_response = {
                "execution_id": str(uuid.uuid4()),
                "workflow_name": "custom-analysis-workflow",
                "status": "running",
                "definition_validated": True,
                "steps_count": 3,
                "estimated_duration": 120
            }

            from .test_fixtures import MockServiceResponse
            execute_definition_response = MockServiceResponse(status_code=202, json_data=definition_execution_response)
            self.mock_framework.http_client.add_response("orchestrator_execute_definition", execute_definition_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Execute workflow from definition
                definition_json = json.dumps(workflow_definition)
                await self.cli.orchestrator_command("execute", definition=definition_json)

                output = mock_stdout.getvalue()

                # Verify definition execution
                assert "🚀 Workflow Execution Started:" in output
                assert "custom-analysis-workflow" in output
                assert "definition_validated" in output
                assert "3" in output  # steps count
                assert "120" in output  # estimated duration

    @pytest.mark.asyncio
    async def test_workflow_error_scenarios_and_recovery(self):
        """Test various workflow error scenarios and recovery mechanisms"""
        with self.mock_framework.mock_cli_environment():
            # Test different error scenarios
            error_scenarios = [
                {
                    "name": "service_unavailable",
                    "error": "Service temporarily unavailable",
                    "recovery": "automatic_retry",
                    "expected_message": "Service temporarily unavailable"
                },
                {
                    "name": "data_validation_error",
                    "error": "Input data validation failed",
                    "recovery": "manual_intervention",
                    "expected_message": "Input data validation failed"
                },
                {
                    "name": "resource_exhaustion",
                    "error": "System resources exhausted",
                    "recovery": "scale_resources",
                    "expected_message": "System resources exhausted"
                }
            ]

            for scenario in error_scenarios:
                execution_id = str(uuid.uuid4())

                # Setup error response
                error_response_data = {
                    "execution_id": execution_id,
                    "status": "error",
                    "error": scenario["error"],
                    "error_type": scenario["name"],
                    "recovery_strategy": scenario["recovery"],
                    "retry_count": 1,
                    "max_retries": 3
                }

                from .test_fixtures import MockServiceResponse
                error_response = MockServiceResponse(status_code=500, json_data=error_response_data)
                self.mock_framework.http_client.add_response(f"orchestrator_error_{scenario['name']}", error_response)

                # Setup recovery response
                recovery_response_data = {
                    "execution_id": execution_id,
                    "status": "recovering",
                    "recovery_strategy": scenario["recovery"],
                    "recovery_progress": 50,
                    "estimated_completion": "2024-01-20T10:10:00Z"
                }
                recovery_response = MockServiceResponse(status_code=200, json_data=recovery_response_data)
                self.mock_framework.http_client.add_response(f"orchestrator_recovery_{scenario['name']}", recovery_response)

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    # Execute workflow that encounters error
                    await self.cli.orchestrator_command("execute", id=str(uuid.uuid4()))

                    # Check error status
                    await self.cli.orchestrator_command("execution-status", id=execution_id)

                    output = mock_stdout.getvalue()

                    # Verify error handling
                    assert scenario["expected_message"] in output
                    assert "error" in output
                    assert scenario["recovery"] in output

    def test_orchestrator_cli_help_and_validation(self):
        """Test orchestrator CLI help and input validation"""
        # Test unknown command
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            asyncio.run(self.cli.orchestrator_command("unknown_command"))

            output = mock_stdout.getvalue()
            assert "❌ Unknown orchestrator command: unknown_command" in output
            assert "Available commands:" in output
            assert "peers, sync, health, config" in output

        # Test execute without required parameters
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            asyncio.run(self.cli.orchestrator_command("execute"))

            output = mock_stdout.getvalue()
            assert "❌ Workflow execution requires --id or --definition parameter" in output

        # Test execution-status without ID
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            asyncio.run(self.cli.orchestrator_command("execution-status"))

            output = mock_stdout.getvalue()
            assert "❌ Execution ID required" in output

        # Test cancel-execution without ID
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            asyncio.run(self.cli.orchestrator_command("cancel-execution"))

            output = mock_stdout.getvalue()
            assert "❌ Execution ID required" in output


if __name__ == "__main__":
    # Run CLI workflow execution tests
    test_instance = TestCLIWorkflowExecution()
    test_instance.setup_method()

    print("🔄 Running CLI Workflow Execution Tests...")
    print("=" * 55)

    # Test basic functionality
    try:
        asyncio.run(test_instance.test_complete_workflow_lifecycle())
        print("✅ Complete workflow lifecycle: PASSED")
    except Exception as e:
        print(f"❌ Complete workflow lifecycle: FAILED - {e}")

    try:
        asyncio.run(test_instance.test_workflow_template_usage())
        print("✅ Workflow template usage: PASSED")
    except Exception as e:
        print(f"❌ Workflow template usage: FAILED - {e}")

    try:
        asyncio.run(test_instance.test_workflow_execution_monitoring())
        print("✅ Workflow execution monitoring: PASSED")
    except Exception as e:
        print(f"❌ Workflow execution monitoring: FAILED - {e}")

    print("\n🏁 CLI Workflow Execution Tests completed!")
