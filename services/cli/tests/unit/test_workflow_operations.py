"""Unit Tests for Workflow Operations in CLI Service.

This module tests workflow operation capabilities including:
- Workflow creation and configuration
- Multi-step workflow execution
- Workflow state management and monitoring
- Error handling and recovery in workflows
- Workflow templates and reuse
- Parallel execution and dependencies

Tests cover the complete workflow orchestration system within the CLI service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

from modules.managers.workflow_manager import WorkflowManager
from modules.models import WorkflowExecution, CommandResult


class TestWorkflowCreation:
    """Test Workflow Creation functionality."""

    @pytest.fixture
    def workflow_manager(self, mock_service_adapter):
        """Create workflow manager instance."""
        return WorkflowManager(service_adapter=mock_service_adapter)

    def test_basic_workflow_creation(self, workflow_manager):
        """Test basic workflow creation."""
        workflow_config = {
            "name": "simple_data_pipeline",
            "description": "Simple data processing pipeline",
            "steps": [
                {
                    "id": "extract",
                    "name": "Extract Data",
                    "command": "doc-store retrieve",
                    "args": {"document_id": "doc_123"},
                    "timeout": 30
                },
                {
                    "id": "process",
                    "name": "Process Data",
                    "command": "interpreter analyze",
                    "args": {"content": "{extract.result}"},
                    "depends_on": ["extract"]
                }
            ]
        }

        result = workflow_manager.create_workflow(workflow_config)

        assert result["success"] is True
        assert "workflow_id" in result
        assert result["workflow"]["name"] == workflow_config["name"]
        assert len(result["workflow"]["steps"]) == len(workflow_config["steps"])

    def test_workflow_validation(self, workflow_manager):
        """Test workflow validation."""
        # Valid workflow
        valid_config = {
            "name": "valid_workflow",
            "steps": [
                {"id": "step1", "command": "status", "args": {}},
                {"id": "step2", "command": "health", "args": {}, "depends_on": ["step1"]}
            ]
        }

        result = workflow_manager.validate_workflow(valid_config)
        assert result["valid"] is True

        # Invalid workflows
        invalid_configs = [
            # Missing name
            {"steps": [{"command": "status"}]},
            # Empty steps
            {"name": "empty", "steps": []},
            # Circular dependency
            {
                "name": "circular",
                "steps": [
                    {"id": "a", "command": "status", "depends_on": ["b"]},
                    {"id": "b", "command": "health", "depends_on": ["a"]}
                ]
            },
            # Invalid command
            {"name": "invalid", "steps": [{"command": "invalid_command"}]}
        ]

        for invalid_config in invalid_configs:
            result = workflow_manager.validate_workflow(invalid_config)
            assert result["valid"] is False
            assert "errors" in result

    def test_workflow_dependency_resolution(self, workflow_manager):
        """Test workflow dependency resolution."""
        workflow_config = {
            "name": "complex_workflow",
            "steps": [
                {"id": "init", "command": "status", "depends_on": []},
                {"id": "process_a", "command": "analyze", "depends_on": ["init"]},
                {"id": "process_b", "command": "analyze", "depends_on": ["init"]},
                {"id": "combine", "command": "merge", "depends_on": ["process_a", "process_b"]},
                {"id": "finalize", "command": "store", "depends_on": ["combine"]}
            ]
        }

        dependency_result = workflow_manager.resolve_dependencies(workflow_config["steps"])

        assert dependency_result["success"] is True
        assert "execution_order" in dependency_result

        execution_order = dependency_result["execution_order"]

        # Verify dependency ordering
        init_index = execution_order.index("init")
        process_a_index = execution_order.index("process_a")
        process_b_index = execution_order.index("process_b")
        combine_index = execution_order.index("combine")
        finalize_index = execution_order.index("finalize")

        assert init_index < process_a_index
        assert init_index < process_b_index
        assert process_a_index < combine_index
        assert process_b_index < combine_index
        assert combine_index < finalize_index

    def test_workflow_template_application(self, workflow_manager):
        """Test workflow template application."""
        template = {
            "name": "data_analysis_template",
            "variables": ["data_source", "analysis_type"],
            "steps": [
                {
                    "id": "load",
                    "command": "doc-store retrieve",
                    "args": {"document_id": "{{data_source}}"}
                },
                {
                    "id": "analyze",
                    "command": "interpreter analyze",
                    "args": {"content": "{load.result}", "type": "{{analysis_type}}"}
                }
            ]
        }

        parameters = {
            "data_source": "doc_456",
            "analysis_type": "sentiment"
        }

        result = workflow_manager.apply_workflow_template(template, parameters)

        assert result["success"] is True
        assert "workflow" in result

        workflow = result["workflow"]

        # Should substitute variables
        load_step = next(step for step in workflow["steps"] if step["id"] == "load")
        assert load_step["args"]["document_id"] == "doc_456"

        analyze_step = next(step for step in workflow["steps"] if step["id"] == "analyze")
        assert analyze_step["args"]["type"] == "sentiment"

    def test_workflow_parameter_validation(self, workflow_manager):
        """Test workflow parameter validation."""
        workflow_with_params = {
            "name": "parameterized_workflow",
            "parameters": {
                "input_file": {"type": "string", "required": True},
                "output_format": {"type": "enum", "values": ["json", "xml", "csv"], "default": "json"},
                "timeout": {"type": "integer", "min": 1, "max": 300, "default": 30}
            },
            "steps": [
                {"command": "process", "args": {"file": "{input_file}", "format": "{output_format}"}}
            ]
        }

        # Valid parameters
        valid_params = {
            "input_file": "data.txt",
            "output_format": "xml",
            "timeout": 60
        }

        result = workflow_manager.validate_workflow_parameters(workflow_with_params, valid_params)
        assert result["valid"] is True

        # Invalid parameters
        invalid_params_list = [
            {"input_file": "", "output_format": "xml"},  # Missing required
            {"input_file": "data.txt", "output_format": "html"},  # Invalid enum
            {"input_file": "data.txt", "timeout": 500}  # Out of range
        ]

        for invalid_params in invalid_params_list:
            result = workflow_manager.validate_workflow_parameters(workflow_with_params, invalid_params)
            assert result["valid"] is False


class TestWorkflowExecution:
    """Test Workflow Execution functionality."""

    @pytest.fixture
    def workflow_executor(self, mock_service_adapter):
        """Create workflow executor instance."""
        return WorkflowManager(service_adapter=mock_service_adapter)

    def test_linear_workflow_execution(self, workflow_executor):
        """Test linear workflow execution."""
        workflow = {
            "name": "linear_workflow",
            "steps": [
                {
                    "id": "step1",
                    "command": "status",
                    "args": {"service": "interpreter"}
                },
                {
                    "id": "step2",
                    "command": "health",
                    "args": {"service": "orchestrator"}
                },
                {
                    "id": "step3",
                    "command": "list",
                    "args": {"type": "documents"}
                }
            ]
        }

        execution_result = workflow_executor.execute_workflow(workflow)

        assert execution_result["success"] is True
        assert "execution_id" in execution_result
        assert "step_results" in execution_result
        assert len(execution_result["step_results"]) == len(workflow["steps"])

        # All steps should have succeeded
        for step_result in execution_result["step_results"]:
            assert step_result["success"] is True

    def test_parallel_workflow_execution(self, workflow_executor):
        """Test parallel workflow execution."""
        workflow = {
            "name": "parallel_workflow",
            "execution_mode": "parallel",
            "steps": [
                {
                    "id": "health_check_1",
                    "command": "health",
                    "args": {"service": "interpreter"},
                    "parallel_group": "health_checks"
                },
                {
                    "id": "health_check_2",
                    "command": "health",
                    "args": {"service": "orchestrator"},
                    "parallel_group": "health_checks"
                },
                {
                    "id": "status_check",
                    "command": "status",
                    "args": {"service": "all"},
                    "depends_on": ["health_check_1", "health_check_2"]
                }
            ]
        }

        execution_result = workflow_executor.execute_workflow(workflow)

        assert execution_result["success"] is True
        assert execution_result["execution_mode"] == "parallel"

        step_results = execution_result["step_results"]

        # Parallel steps should have similar execution times
        parallel_steps = [s for s in step_results if s["step_id"].startswith("health_check")]
        if len(parallel_steps) == 2:
            time_diff = abs(parallel_steps[0]["execution_time_ms"] - parallel_steps[1]["execution_time_ms"])
            # Should execute in parallel (small time difference)
            assert time_diff < 100  # Less than 100ms difference

    def test_workflow_execution_with_error_handling(self, workflow_executor):
        """Test workflow execution with error handling."""
        # Mock a step that will fail
        def failing_step(*args, **kwargs):
            if kwargs.get("command") == "failing_command":
                raise Exception("Step failed")
            return {"success": True, "result": "ok"}

        with patch.object(workflow_executor.service_adapter, 'execute_command', side_effect=failing_step):
            workflow = {
                "name": "error_handling_workflow",
                "error_handling": {
                    "fail_fast": False,
                    "continue_on_error": True,
                    "retry_failed_steps": True,
                    "max_retries": 2
                },
                "steps": [
                    {"id": "success_step", "command": "status", "args": {}},
                    {"id": "failing_step", "command": "failing_command", "args": {}},
                    {"id": "recovery_step", "command": "status", "args": {}}
                ]
            }

            execution_result = workflow_executor.execute_workflow(workflow)

            assert execution_result["success"] is True  # Workflow succeeds despite failed step
            assert execution_result["partial_success"] is True

            step_results = execution_result["step_results"]

            # Find the failing step
            failing_step_result = next(s for s in step_results if s["step_id"] == "failing_step")
            assert failing_step_result["success"] is False
            assert "error" in failing_step_result

            # Successful steps should still execute
            success_steps = [s for s in step_results if s["step_id"] != "failing_step"]
            assert all(s["success"] is True for s in success_steps)

    def test_workflow_execution_with_timeouts(self, workflow_executor):
        """Test workflow execution with step timeouts."""
        import asyncio

        async def slow_step(*args, **kwargs):
            await asyncio.sleep(2)  # 2 seconds
            return {"success": True, "result": "completed"}

        with patch.object(workflow_executor.service_adapter, 'execute_command', side_effect=slow_step):
            workflow = {
                "name": "timeout_workflow",
                "steps": [
                    {
                        "id": "fast_step",
                        "command": "status",
                        "args": {},
                        "timeout": 5
                    },
                    {
                        "id": "slow_step",
                        "command": "slow_command",
                        "args": {},
                        "timeout": 1  # 1 second timeout
                    }
                ]
            }

            execution_result = workflow_executor.execute_workflow(workflow)

            # Workflow should handle timeouts gracefully
            step_results = execution_result["step_results"]

            fast_step = next(s for s in step_results if s["step_id"] == "fast_step")
            slow_step = next(s for s in step_results if s["step_id"] == "slow_step")

            # Fast step should succeed
            assert fast_step["success"] is True

            # Slow step should fail due to timeout
            assert slow_step["success"] is False
            assert "timeout" in str(slow_step.get("error", "")).lower()

    def test_workflow_result_chaining(self, workflow_executor):
        """Test workflow result chaining between steps."""
        workflow = {
            "name": "chaining_workflow",
            "steps": [
                {
                    "id": "get_data",
                    "command": "doc-store retrieve",
                    "args": {"document_id": "doc_123"}
                },
                {
                    "id": "extract_content",
                    "command": "extract",
                    "args": {"data": "{get_data.result.content}"}
                },
                {
                    "id": "analyze_content",
                    "command": "interpreter analyze",
                    "args": {"content": "{extract_content.result}"}
                },
                {
                    "id": "store_result",
                    "command": "doc-store store",
                    "args": {"content": "{analyze_content.result}", "title": "Analysis Result"}
                }
            ]
        }

        execution_result = workflow_executor.execute_workflow(workflow)

        assert execution_result["success"] is True

        step_results = execution_result["step_results"]

        # Verify result chaining
        get_data_step = next(s for s in step_results if s["step_id"] == "get_data")
        extract_step = next(s for s in step_results if s["step_id"] == "extract_content")
        analyze_step = next(s for s in step_results if s["step_id"] == "analyze_content")
        store_step = next(s for s in step_results if s["step_id"] == "store_result")

        # Each step should have received the correct input from previous step
        assert extract_step["input"]["data"] == get_data_step["result"]["content"]
        assert analyze_step["input"]["content"] == extract_step["result"]
        assert store_step["input"]["content"] == analyze_step["result"]

    def test_workflow_execution_monitoring(self, workflow_executor):
        """Test workflow execution monitoring and progress tracking."""
        workflow = {
            "name": "monitored_workflow",
            "steps": [
                {"id": "step1", "command": "status", "args": {}},
                {"id": "step2", "command": "health", "args": {}},
                {"id": "step3", "command": "list", "args": {}}
            ]
        }

        # Execute workflow and monitor progress
        execution_result = workflow_executor.execute_workflow(workflow)

        assert execution_result["success"] is True
        assert "monitoring_data" in execution_result

        monitoring = execution_result["monitoring_data"]

        # Should track execution metrics
        assert "start_time" in monitoring
        assert "end_time" in monitoring
        assert "total_execution_time_ms" in monitoring
        assert monitoring["total_execution_time_ms"] > 0

        # Should track step-level metrics
        assert "step_metrics" in monitoring
        step_metrics = monitoring["step_metrics"]

        assert len(step_metrics) == len(workflow["steps"])

        for step_metric in step_metrics:
            assert "step_id" in step_metric
            assert "execution_time_ms" in step_metric
            assert "success" in step_metric

    def test_workflow_rollback_and_recovery(self, workflow_executor):
        """Test workflow rollback and recovery mechanisms."""
        workflow = {
            "name": "rollback_workflow",
            "rollback_enabled": True,
            "steps": [
                {
                    "id": "create_resource",
                    "command": "create",
                    "args": {"resource": "temp_data"},
                    "rollback_command": "delete",
                    "rollback_args": {"resource": "temp_data"}
                },
                {
                    "id": "process_data",
                    "command": "process",
                    "args": {"data": "temp_data"}
                },
                {
                    "id": "failing_step",
                    "command": "failing_command",
                    "args": {}
                }
            ]
        }

        # Mock failing step
        def failing_command(*args, **kwargs):
            if kwargs.get("command") == "failing_command":
                raise Exception("Step failed")
            return {"success": True, "result": "ok"}

        with patch.object(workflow_executor.service_adapter, 'execute_command', side_effect=failing_command):
            execution_result = workflow_executor.execute_workflow(workflow)

            # Workflow should fail
            assert execution_result["success"] is False

            # Should have rollback information
            assert "rollback_executed" in execution_result
            assert execution_result["rollback_executed"] is True

            # Should have rollback results
            assert "rollback_results" in execution_result
            rollback_results = execution_result["rollback_results"]

            # Should have rolled back the create_resource step
            create_rollback = next((r for r in rollback_results if r["step_id"] == "create_resource"), None)
            assert create_rollback is not None
            assert create_rollback["rollback_success"] is True


class TestWorkflowStateManagement:
    """Test Workflow State Management functionality."""

    @pytest.fixture
    def state_manager(self, mock_repository):
        """Create workflow state manager instance."""
        return WorkflowManager(repository=mock_repository)

    def test_workflow_state_transitions(self, state_manager):
        """Test workflow state transition validation."""
        workflow_id = str(uuid.uuid4())

        # Valid state transitions
        valid_transitions = [
            ("created", "queued"),
            ("queued", "running"),
            ("running", "completed"),
            ("running", "failed"),
            ("failed", "retrying"),
            ("retrying", "completed"),
            ("completed", "archived")
        ]

        for from_state, to_state in valid_transitions:
            transition_result = state_manager.validate_state_transition(workflow_id, from_state, to_state)
            assert transition_result["valid"] is True

        # Invalid state transitions
        invalid_transitions = [
            ("created", "completed"),  # Skip states
            ("completed", "running"),  # Cannot restart
            ("failed", "running"),     # Must go through retrying
            ("archived", "running")    # Cannot unarchive
        ]

        for from_state, to_state in invalid_transitions:
            transition_result = state_manager.validate_state_transition(workflow_id, from_state, to_state)
            assert transition_result["valid"] is False

    def test_workflow_persistence_and_recovery(self, state_manager, sample_workflow_execution):
        """Test workflow persistence and recovery."""
        execution = sample_workflow_execution

        # Persist workflow state
        persist_result = state_manager.persist_workflow_state(execution)

        assert persist_result["success"] is True
        assert "state_id" in persist_result

        # Recover workflow state
        recovery_result = state_manager.recover_workflow_state(execution.workflow_id)

        assert recovery_result["success"] is True
        recovered_execution = recovery_result["execution"]

        # Should recover all execution details
        assert recovered_execution["workflow_id"] == execution.workflow_id
        assert recovered_execution["status"] == execution.status
        assert len(recovered_execution["step_results"]) == len(execution.step_results)

    def test_workflow_checkpointing(self, state_manager):
        """Test workflow checkpointing for resumability."""
        workflow_id = str(uuid.uuid4())

        checkpoints = [
            {"step": "init", "progress": 10, "data": {"initialized": True}},
            {"step": "process", "progress": 50, "data": {"processed_items": 25}},
            {"step": "finalize", "progress": 90, "data": {"finalized": True}}
        ]

        # Create checkpoints
        for checkpoint in checkpoints:
            checkpoint_result = state_manager.create_checkpoint(
                workflow_id, checkpoint["step"], checkpoint["progress"], checkpoint["data"]
            )
            assert checkpoint_result["success"] is True

        # Resume from latest checkpoint
        resume_result = state_manager.resume_from_checkpoint(workflow_id)

        assert resume_result["success"] is True
        assert "checkpoint" in resume_result

        latest_checkpoint = resume_result["checkpoint"]
        assert latest_checkpoint["step"] == "finalize"
        assert latest_checkpoint["progress"] == 90
        assert latest_checkpoint["data"]["finalized"] is True

    def test_workflow_concurrent_execution_handling(self, state_manager):
        """Test handling of concurrent workflow executions."""
        workflow_template = {
            "name": "concurrent_test_workflow",
            "steps": [
                {"id": "shared_step", "command": "status", "args": {}},
                {"id": "parallel_step_1", "command": "analyze", "args": {"data": "input1"}},
                {"id": "parallel_step_2", "command": "analyze", "args": {"data": "input2"}}
            ]
        }

        # Execute multiple instances concurrently
        execution_ids = []
        for i in range(5):
            execution_result = state_manager.execute_workflow(workflow_template)
            assert execution_result["success"] is True
            execution_ids.append(execution_result["execution_id"])

        # Verify all executions completed independently
        for execution_id in execution_ids:
            status_result = state_manager.get_workflow_status(execution_id)
            assert status_result["status"] == "completed"

        # Verify no cross-contamination between executions
        all_results = []
        for execution_id in execution_ids:
            details = state_manager.get_workflow_details(execution_id)
            all_results.append(details["step_results"])

        # All executions should have same number of steps
        assert len(set(len(results) for results in all_results)) == 1

    def test_workflow_resource_management(self, state_manager):
        """Test workflow resource management and cleanup."""
        workflow_id = str(uuid.uuid4())

        # Simulate workflow resource usage
        resources = {
            "temporary_files": ["/tmp/workflow_123_file1.txt", "/tmp/workflow_123_file2.json"],
            "cache_entries": ["cache_key_1", "cache_key_2"],
            "database_connections": ["conn_1", "conn_2"],
            "memory_allocations": ["mem_block_1", "mem_block_2"]
        }

        # Track resource allocation
        allocation_result = state_manager.allocate_workflow_resources(workflow_id, resources)
        assert allocation_result["success"] is True

        # Simulate workflow completion
        completion_result = state_manager.complete_workflow(workflow_id, {"success": True})

        assert completion_result["success"] is True
        assert "resources_cleaned" in completion_result

        # Verify resource cleanup
        cleanup_info = completion_result["resources_cleaned"]
        assert cleanup_info["temporary_files_removed"] == len(resources["temporary_files"])
        assert cleanup_info["cache_entries_cleared"] == len(resources["cache_entries"])
        assert cleanup_info["connections_closed"] == len(resources["database_connections"])

    def test_workflow_performance_analytics(self, state_manager):
        """Test workflow performance analytics and optimization."""
        # Simulate multiple workflow executions with performance data
        performance_data = []
        for i in range(10):
            execution = {
                "workflow_id": str(uuid.uuid4()),
                "total_execution_time_ms": 1000 + (i * 100),  # Increasing times
                "steps": [
                    {"step_id": "step1", "execution_time_ms": 200 + (i * 10)},
                    {"step_id": "step2", "execution_time_ms": 300 + (i * 15)},
                    {"step_id": "step3", "execution_time_ms": 500 + (i * 25)}
                ],
                "resource_usage": {
                    "cpu_percent": 45 + (i * 2),
                    "memory_mb": 128 + (i * 8)
                }
            }
            performance_data.append(execution)

        analytics_result = state_manager.analyze_workflow_performance(performance_data)

        assert analytics_result["success"] is True
        assert "performance_metrics" in analytics_result
        assert "bottlenecks" in analytics_result
        assert "optimization_recommendations" in analytics_result

        metrics = analytics_result["performance_metrics"]

        # Should calculate aggregate statistics
        assert "average_execution_time_ms" in metrics
        assert "median_execution_time_ms" in metrics
        assert "p95_execution_time_ms" in metrics

        # Should identify performance trends
        assert "performance_trend" in metrics
        assert metrics["performance_trend"] in ["improving", "degrading", "stable"]

        # Should identify bottlenecks
        bottlenecks = analytics_result["bottlenecks"]
        assert len(bottlenecks) > 0

        # Step 3 should likely be identified as a bottleneck (longest execution time)
        step_bottlenecks = [b for b in bottlenecks if "step" in b["component"]]
        assert len(step_bottlenecks) > 0

        # Should provide optimization recommendations
        recommendations = analytics_result["optimization_recommendations"]
        assert len(recommendations) > 0

        # Should include common optimization types
        opt_types = [rec["type"] for rec in recommendations]
        expected_opts = ["parallelization", "caching", "resource_optimization", "step_optimization"]
        assert any(opt in " ".join(opt_types).lower() for opt in expected_opts)
