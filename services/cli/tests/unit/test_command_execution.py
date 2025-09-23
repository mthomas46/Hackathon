"""Unit Tests for Command Execution in CLI Service.

This module tests command execution capabilities including:
- Command parsing and validation
- Argument processing and type checking
- Command execution with service coordination
- Error handling and recovery
- Command completion and suggestions
- Execution timing and performance monitoring

Tests cover the core command execution pipeline within the CLI service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from argparse import Namespace

from modules.cli_commands import CLICommands
from modules.handlers.service_actions import ServiceActions
from modules.managers.workflow_manager import WorkflowManager
from modules.models import CommandResult


class TestCommandParsing:
    """Test Command Parsing functionality."""

    @pytest.fixture
    def cli_commands(self):
        """Create CLI commands instance."""
        return CLICommands()

    def test_basic_command_parsing(self, cli_commands):
        """Test basic command parsing."""
        # Test status command
        args = cli_commands.parse_args(["status", "--service", "interpreter"])
        assert args.command == "status"
        assert args.service == "interpreter"
        assert args.verbose is False

        # Test workflow command
        args = cli_commands.parse_args(["workflow", "list", "--format", "json"])
        assert args.command == "workflow"
        assert args.action == "list"
        assert args.format == "json"

    def test_command_validation(self, cli_commands):
        """Test command validation."""
        # Valid commands
        valid_commands = [
            ["status", "--service", "interpreter"],
            ["workflow", "create", "--name", "test"],
            ["service", "health", "--all"],
            ["config", "show", "--section", "services"]
        ]

        for cmd in valid_commands:
            args = cli_commands.parse_args(cmd)
            assert args is not None

        # Invalid commands
        invalid_commands = [
            ["invalid_command"],
            ["status", "--invalid_option"],
            ["workflow", "invalid_action"]
        ]

        for cmd in invalid_commands:
            with pytest.raises(SystemExit):  # argparse exits on invalid args
                cli_commands.parse_args(cmd)

    def test_argument_type_validation(self, cli_commands):
        """Test argument type validation."""
        # Test integer arguments
        args = cli_commands.parse_args(["workflow", "execute", "--timeout", "30"])
        assert isinstance(args.timeout, int)
        assert args.timeout == 30

        # Test boolean flags
        args = cli_commands.parse_args(["status", "--verbose", "--json"])
        assert args.verbose is True
        assert args.json is True

        # Test list arguments
        args = cli_commands.parse_args(["service", "start", "interpreter", "orchestrator"])
        assert isinstance(args.services, list)
        assert "interpreter" in args.services
        assert "orchestrator" in args.services

    def test_command_help_generation(self, cli_commands):
        """Test command help generation."""
        help_text = cli_commands.get_help_text("status")
        assert "status" in help_text.lower()
        assert "check" in help_text.lower() or "service" in help_text.lower()

        help_text = cli_commands.get_help_text("workflow")
        assert "workflow" in help_text.lower()
        assert "create" in help_text.lower() or "execute" in help_text.lower()

    def test_command_completion_suggestions(self, cli_commands):
        """Test command completion suggestions."""
        # Partial command completion
        suggestions = cli_commands.get_completion_suggestions("stat")
        assert "status" in suggestions

        suggestions = cli_commands.get_completion_suggestions("work")
        assert "workflow" in suggestions

        # Argument completion
        suggestions = cli_commands.get_completion_suggestions("status --service ")
        expected_services = ["interpreter", "orchestrator", "doc_store", "all"]
        for service in expected_services:
            assert service in suggestions

    def test_command_alias_support(self, cli_commands):
        """Test command alias support."""
        # Test aliases
        aliases = {
            "st": "status",
            "wf": "workflow",
            "svc": "service",
            "cfg": "config"
        }

        for alias, command in aliases.items():
            args = cli_commands.parse_args([alias, "--help"])
            # Should be treated as the full command
            assert args.command == command or hasattr(args, command)


class TestCommandExecution:
    """Test Command Execution functionality."""

    @pytest.fixture
    def service_actions(self, mock_service_adapter):
        """Create service actions instance."""
        return ServiceActions(service_adapter=mock_service_adapter)

    def test_status_command_execution(self, service_actions):
        """Test status command execution."""
        result = service_actions.execute_status_command({"service": "interpreter"})

        assert result["success"] is True
        assert "status" in result
        assert "services" in result
        assert isinstance(result["services"], list)

    def test_service_health_check_execution(self, service_actions):
        """Test service health check execution."""
        result = service_actions.execute_health_check({"service": "interpreter", "detailed": True})

        assert result["success"] is True
        assert "health_status" in result
        assert "response_time_ms" in result
        assert "checks_performed" in result

        # Detailed check should include more information
        assert len(result["checks_performed"]) > 1

    def test_workflow_command_execution(self, service_actions):
        """Test workflow command execution."""
        workflow_config = {
            "name": "test_workflow",
            "steps": [
                {"command": "status", "args": {"service": "interpreter"}},
                {"command": "health", "args": {"service": "orchestrator"}}
            ]
        }

        result = service_actions.execute_workflow_command(workflow_config)

        assert result["success"] is True
        assert "workflow_id" in result
        assert "execution_status" in result
        assert "steps_completed" in result
        assert result["steps_completed"] == len(workflow_config["steps"])

    def test_bulk_operation_execution(self, service_actions):
        """Test bulk operation execution."""
        bulk_config = {
            "operation": "status_check",
            "services": ["interpreter", "orchestrator", "doc_store"],
            "parallel": True
        }

        result = service_actions.execute_bulk_operation(bulk_config)

        assert result["success"] is True
        assert "results" in result
        assert len(result["results"]) == len(bulk_config["services"])
        assert "execution_time_ms" in result
        assert "parallel_execution" in result
        assert result["parallel_execution"] is True

    def test_command_execution_error_handling(self, service_actions):
        """Test command execution error handling."""
        # Test with invalid service
        result = service_actions.execute_status_command({"service": "invalid_service"})

        assert result["success"] is False
        assert "error" in result
        assert "error_type" in result

        # Test with network timeout
        with patch.object(service_actions.service_adapter, 'health_check', side_effect=TimeoutError()):
            result = service_actions.execute_health_check({"service": "interpreter"})

            assert result["success"] is False
            assert "timeout" in str(result.get("error", "")).lower()

    def test_command_execution_with_retry_logic(self, service_actions):
        """Test command execution with retry logic."""
        # Mock service that fails twice then succeeds
        call_count = 0
        def failing_service(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Service temporarily unavailable")
            return {"status": "healthy"}

        with patch.object(service_actions.service_adapter, 'health_check', side_effect=failing_service):
            result = service_actions.execute_health_check({
                "service": "interpreter",
                "retry_attempts": 3,
                "retry_delay": 0.1
            })

            assert result["success"] is True
            assert call_count == 3  # Should have retried twice

    def test_command_execution_performance_monitoring(self, service_actions):
        """Test command execution performance monitoring."""
        import time

        start_time = time.time()
        result = service_actions.execute_status_command({"service": "interpreter"})
        execution_time = time.time() - start_time

        assert result["success"] is True
        assert "execution_time_ms" in result
        assert result["execution_time_ms"] > 0
        assert result["execution_time_ms"] < 1000  # Should complete within 1 second

        # Verify timing accuracy (within 10% tolerance)
        measured_time_ms = execution_time * 1000
        tolerance = measured_time_ms * 0.1
        assert abs(result["execution_time_ms"] - measured_time_ms) <= tolerance

    def test_command_execution_cancellation(self, service_actions):
        """Test command execution cancellation."""
        import asyncio

        async def slow_operation():
            await asyncio.sleep(2)  # Long running operation
            return {"status": "completed"}

        with patch.object(service_actions.service_adapter, 'execute_operation', side_effect=slow_operation):
            # Execute with short timeout
            result = service_actions.execute_with_timeout(
                {"operation": "slow_operation", "timeout": 0.5}
            )

            assert result["success"] is False
            assert "timeout" in str(result.get("error", "")).lower()
            assert "cancelled" in str(result.get("error", "")).lower()


class TestServiceCoordination:
    """Test Service Coordination functionality."""

    @pytest.fixture
    def service_coordinator(self, mock_orchestrator_adapter, mock_interpreter_adapter):
        """Create service coordinator instance."""
        return ServiceActions(
            orchestrator_adapter=mock_orchestrator_adapter,
            interpreter_adapter=mock_interpreter_adapter
        )

    def test_cross_service_workflow_execution(self, service_coordinator):
        """Test workflow execution across multiple services."""
        workflow = {
            "name": "document_analysis_workflow",
            "steps": [
                {
                    "service": "doc_store",
                    "command": "retrieve",
                    "args": {"document_id": "doc_123"}
                },
                {
                    "service": "interpreter",
                    "command": "analyze",
                    "args": {"content": "{previous_result.content}"}
                },
                {
                    "service": "orchestrator",
                    "command": "store_result",
                    "args": {"analysis": "{previous_result.analysis}"}
                }
            ]
        }

        result = service_coordinator.execute_cross_service_workflow(workflow)

        assert result["success"] is True
        assert "workflow_id" in result
        assert "step_results" in result
        assert len(result["step_results"]) == len(workflow["steps"])

        # Verify step chaining (each step should have access to previous results)
        for i, step_result in enumerate(result["step_results"]):
            if i > 0:
                assert "previous_result" in step_result["context"]

    def test_service_dependency_resolution(self, service_coordinator):
        """Test service dependency resolution."""
        service_dependencies = {
            "interpreter": ["llm_gateway", "orchestrator"],
            "doc_store": ["database", "file_storage"],
            "orchestrator": ["redis", "database"]
        }

        resolution_result = service_coordinator.resolve_service_dependencies(
            ["interpreter", "doc_store"], service_dependencies
        )

        assert resolution_result["success"] is True
        assert "execution_order" in resolution_result
        assert "dependency_graph" in resolution_result

        execution_order = resolution_result["execution_order"]

        # Orchestrator should come before interpreter (dependency)
        orch_index = execution_order.index("orchestrator")
        interp_index = execution_order.index("interpreter")
        assert orch_index < interp_index

        # Database should come before both doc_store and orchestrator
        db_index = execution_order.index("database")
        assert db_index < orch_index
        assert db_index < execution_order.index("doc_store")

    def test_service_fallback_and_recovery(self, service_coordinator):
        """Test service fallback and recovery mechanisms."""
        # Configure primary and fallback services
        service_config = {
            "primary": "interpreter",
            "fallback": "backup_interpreter",
            "retry_policy": {
                "max_attempts": 3,
                "backoff_factor": 2,
                "timeout_ms": 5000
            }
        }

        # Mock primary service failure, fallback success
        call_log = []

        def primary_service(*args, **kwargs):
            call_log.append("primary_attempt")
            raise ConnectionError("Primary service unavailable")

        def fallback_service(*args, **kwargs):
            call_log.append("fallback_attempt")
            return {"status": "success", "fallback_used": True}

        with patch.object(service_coordinator.interpreter_adapter, 'analyze_text', side_effect=primary_service), \
             patch.object(service_coordinator, 'get_fallback_service', return_value=fallback_service):

            result = service_coordinator.execute_with_fallback(
                {"command": "analyze_text", "args": {"content": "test"}},
                service_config
            )

            assert result["success"] is True
            assert result["fallback_used"] is True
            assert len(call_log) == 2  # Primary + fallback
            assert "primary_attempt" in call_log
            assert "fallback_attempt" in call_log

    def test_service_load_balancing(self, service_coordinator):
        """Test load balancing across service instances."""
        service_instances = [
            {"id": "inst_1", "load": 30, "capacity": 100, "response_time": 200},
            {"id": "inst_2", "load": 80, "capacity": 100, "response_time": 150},
            {"id": "inst_3", "load": 10, "capacity": 100, "response_time": 300}
        ]

        requests = ["req_1", "req_2", "req_3", "req_4", "req_5"]

        load_balance_result = service_coordinator.balance_service_load(service_instances, requests)

        assert load_balance_result["success"] is True
        assert "assignments" in load_balance_result
        assert "load_distribution" in load_balance_result

        assignments = load_balance_result["assignments"]

        # Should distribute based on load and capacity
        instance_loads = {}
        for assignment in assignments:
            instance = assignment["assigned_instance"]
            instance_loads[instance] = instance_loads.get(instance, 0) + 1

        # Instance with lowest load should get more requests
        assert instance_loads["inst_3"] >= instance_loads["inst_1"]  # 10% vs 30% load

        # Instance with high load should get fewer requests
        assert instance_loads["inst_2"] <= instance_loads["inst_1"]  # 80% vs 30% load

    def test_service_health_monitoring(self, service_coordinator):
        """Test service health monitoring and alerting."""
        health_metrics = {
            "interpreter": {
                "response_time_ms": 250,
                "error_rate": 0.02,
                "uptime_percent": 99.5,
                "active_connections": 45
            },
            "orchestrator": {
                "response_time_ms": 180,
                "error_rate": 0.05,
                "uptime_percent": 98.2,
                "active_connections": 67
            },
            "doc_store": {
                "response_time_ms": 120,
                "error_rate": 0.01,
                "uptime_percent": 99.9,
                "active_connections": 23
            }
        }

        monitoring_result = service_coordinator.monitor_service_health(health_metrics)

        assert monitoring_result["success"] is True
        assert "health_status" in monitoring_result
        assert "alerts" in monitoring_result
        assert "recommendations" in monitoring_result

        # Should identify services needing attention
        alerts = monitoring_result["alerts"]
        orchestrator_alerts = [a for a in alerts if "orchestrator" in a["service"]]
        assert len(orchestrator_alerts) > 0  # High error rate

        # Should provide health score
        health_status = monitoring_result["health_status"]
        assert "overall_score" in health_status
        assert 0 <= health_status["overall_score"] <= 100

    def test_service_configuration_management(self, service_coordinator):
        """Test service configuration management."""
        config_updates = {
            "interpreter": {
                "timeout": 60,
                "max_retries": 5,
                "cache_enabled": True
            },
            "orchestrator": {
                "worker_threads": 10,
                "queue_size": 1000,
                "health_check_interval": 30
            }
        }

        config_result = service_coordinator.update_service_configurations(config_updates)

        assert config_result["success"] is True
        assert "updated_services" in config_result
        assert "validation_results" in config_result

        # Should validate configurations
        validation_results = config_result["validation_results"]
        for service in config_updates.keys():
            assert service in validation_results
            assert validation_results[service]["valid"] is True

        # Should return updated service count
        assert len(config_result["updated_services"]) == len(config_updates)

    def test_service_performance_optimization(self, service_coordinator):
        """Test service performance optimization."""
        performance_data = {
            "interpreter": {
                "avg_response_time": 450,
                "throughput": 25,
                "error_rate": 0.02,
                "resource_usage": {"cpu": 65, "memory": 70}
            },
            "orchestrator": {
                "avg_response_time": 320,
                "throughput": 35,
                "error_rate": 0.03,
                "resource_usage": {"cpu": 55, "memory": 60}
            }
        }

        optimization_result = service_coordinator.optimize_service_performance(performance_data)

        assert optimization_result["success"] is True
        assert "optimizations" in optimization_result
        assert "performance_projections" in optimization_result

        optimizations = optimization_result["optimizations"]

        # Should suggest optimizations based on performance data
        for service, service_opts in optimizations.items():
            assert len(service_opts) > 0  # Should have optimization suggestions

            # Common optimizations
            opt_types = [opt["type"] for opt in service_opts]
            expected_opts = ["caching", "load_balancing", "resource_allocation", "connection_pooling"]
            assert any(opt in " ".join(opt_types).lower() for opt in expected_opts)

        # Should project performance improvements
        projections = optimization_result["performance_projections"]
        assert "estimated_improvements" in projections
        assert projections["estimated_improvements"]["response_time_reduction_percent"] > 0
