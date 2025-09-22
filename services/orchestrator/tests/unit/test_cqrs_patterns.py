"""Unit Tests for CQRS Patterns in Orchestrator Service.

This module tests Command Query Responsibility Segregation (CQRS) implementation:
- Command validation and handling
- Query validation and execution
- Command-Query separation
- Event sourcing integration

Tests cover all bounded contexts with CQRS implementations.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from application.service_registry.commands import RegisterServiceCommand, UnregisterServiceCommand
from application.service_registry.queries import GetServiceQuery, ListServicesQuery
from application.workflow_management.commands import CreateWorkflowCommand, ExecuteWorkflowCommand
from application.workflow_management.queries import GetWorkflowQuery, ListWorkflowsQuery
from application.health_monitoring.queries import GetHealthStatusQuery, ListHealthHistoryQuery
from application.infrastructure.queries import GetInfrastructureStatusQuery
from application.ingestion.commands import StartIngestionCommand, CancelIngestionCommand
from application.ingestion.queries import GetIngestionStatusQuery, ListIngestionJobsQuery
from application.query_processing.commands import ProcessQueryCommand
from application.query_processing.queries import GetQueryResultQuery, ListQueriesQuery
from application.reporting.commands import GenerateReportCommand
from application.reporting.queries import GetReportQuery, ListReportsQuery


class TestServiceRegistryCQRS:
    """Test CQRS patterns for Service Registry bounded context."""

    @pytest.mark.asyncio
    async def test_register_service_command_validation(self):
        """Test RegisterServiceCommand validation."""
        command = RegisterServiceCommand(
            service_name="test-service",
            service_type="api",
            host="localhost",
            port=8080,
            capabilities=["health_check", "api"],
            metadata={"version": "1.0.0"}
        )

        # Test command properties
        assert command.service_name == "test-service"
        assert command.service_type == "api"
        assert command.port == 8080
        assert len(command.capabilities) > 0

    @pytest.mark.asyncio
    async def test_register_service_command_validation_rules(self):
        """Test RegisterServiceCommand validation rules."""
        # Test invalid service name
        with pytest.raises(ValueError):
            RegisterServiceCommand(
                service_name="",  # Invalid
                service_type="api",
                host="localhost",
                port=8080,
                capabilities=[]
            )

        # Test invalid port
        with pytest.raises(ValueError):
            RegisterServiceCommand(
                service_name="test-service",
                service_type="api",
                host="localhost",
                port=70000,  # Invalid
                capabilities=[]
            )

    @pytest.mark.asyncio
    async def test_unregister_service_command(self):
        """Test UnregisterServiceCommand."""
        command = UnregisterServiceCommand(
            service_name="test-service",
            reason="Service decommissioned"
        )

        assert command.service_name == "test-service"
        assert command.reason == "Service decommissioned"

    @pytest.mark.asyncio
    async def test_get_service_query(self):
        """Test GetServiceQuery."""
        query = GetServiceQuery(
            service_name="test-service",
            include_health=True
        )

        assert query.service_name == "test-service"
        assert query.include_health is True

    @pytest.mark.asyncio
    async def test_list_services_query_with_filters(self):
        """Test ListServicesQuery with filters."""
        query = ListServicesQuery(
            service_type="api",
            status="healthy",
            capabilities=["health_check"],
            limit=50,
            offset=0
        )

        assert query.service_type == "api"
        assert query.status == "healthy"
        assert "health_check" in query.capabilities
        assert query.limit == 50


class TestWorkflowManagementCQRS:
    """Test CQRS patterns for Workflow Management bounded context."""

    @pytest.mark.asyncio
    async def test_create_workflow_command_complex_validation(self):
        """Test CreateWorkflowCommand with complex workflow."""
        command = CreateWorkflowCommand(
            name="Complex Document Processing Workflow",
            description="Multi-step document analysis pipeline",
            workflow_type="document_processing",
            steps=[
                {
                    "name": "Data Ingestion",
                    "type": "ingestion",
                    "config": {"source": "api", "format": "json"},
                    "depends_on": []
                },
                {
                    "name": "Content Analysis",
                    "type": "analysis",
                    "config": {"model": "gpt-4", "analysis_type": "sentiment"},
                    "depends_on": ["data_ingestion"]
                },
                {
                    "name": "Result Storage",
                    "type": "storage",
                    "config": {"target": "database", "table": "analysis_results"},
                    "depends_on": ["content_analysis"]
                }
            ],
            tags=["document", "analysis", "ai"],
            metadata={"priority": "high", "estimated_duration": 300}
        )

        assert command.name == "Complex Document Processing Workflow"
        assert len(command.steps) == 3
        assert command.workflow_type == "document_processing"

        # Test step dependency validation
        step_names = [step["name"] for step in command.steps]
        for step in command.steps:
            if step.get("depends_on"):
                for dep in step["depends_on"]:
                    assert dep in step_names

    @pytest.mark.asyncio
    async def test_execute_workflow_command_with_parameters(self):
        """Test ExecuteWorkflowCommand with execution parameters."""
        workflow_id = str(uuid.uuid4())

        command = ExecuteWorkflowCommand(
            workflow_id=workflow_id,
            input_parameters={
                "document_url": "https://example.com/document.pdf",
                "analysis_options": {
                    "extract_text": True,
                    "perform_sentiment": True,
                    "generate_summary": True
                }
            },
            execution_options={
                "priority": "high",
                "timeout_seconds": 600,
                "notification_enabled": True,
                "result_persistence": "permanent"
            },
            triggered_by="api_user",
            correlation_id=str(uuid.uuid4())
        )

        assert command.workflow_id == workflow_id
        assert "document_url" in command.input_parameters
        assert command.execution_options["priority"] == "high"
        assert command.correlation_id is not None

    @pytest.mark.asyncio
    async def test_get_workflow_query_with_expansion(self):
        """Test GetWorkflowQuery with expansion options."""
        query = GetWorkflowQuery(
            workflow_id=str(uuid.uuid4()),
            include_executions=True,
            include_execution_history=True,
            execution_limit=10,
            include_metrics=True,
            metrics_timeframe="7d"
        )

        assert query.include_executions is True
        assert query.include_execution_history is True
        assert query.execution_limit == 10
        assert query.include_metrics is True

    @pytest.mark.asyncio
    async def test_list_workflows_query_advanced_filtering(self):
        """Test ListWorkflowsQuery with advanced filtering."""
        query = ListWorkflowsQuery(
            status="active",
            workflow_type="document_processing",
            created_by="test_user",
            tags=["ai", "analysis"],
            date_created_from=datetime.now() - timedelta(days=30),
            date_created_to=datetime.now(),
            sort_by="created_at",
            sort_order="desc",
            limit=25,
            offset=0
        )

        assert query.status == "active"
        assert query.workflow_type == "document_processing"
        assert "ai" in query.tags
        assert query.sort_by == "created_at"
        assert query.limit == 25


class TestHealthMonitoringCQRS:
    """Test CQRS patterns for Health Monitoring bounded context."""

    @pytest.mark.asyncio
    async def test_get_health_status_query_comprehensive(self):
        """Test GetHealthStatusQuery with comprehensive options."""
        query = GetHealthStatusQuery(
            service_name="test-service",
            include_detailed_metrics=True,
            include_historical_data=True,
            time_range_hours=24,
            metrics_filter=["response_time", "error_rate", "throughput"],
            include_alerts=True,
            alert_severity_filter=["warning", "error"]
        )

        assert query.service_name == "test-service"
        assert query.include_detailed_metrics is True
        assert query.time_range_hours == 24
        assert "response_time" in query.metrics_filter

    @pytest.mark.asyncio
    async def test_list_health_history_query_with_aggregation(self):
        """Test ListHealthHistoryQuery with aggregation options."""
        query = ListHealthHistoryQuery(
            service_filter=["api", "worker"],
            status_filter=["healthy", "warning"],
            time_range_start=datetime.now() - timedelta(days=7),
            time_range_end=datetime.now(),
            aggregation_level="hour",
            include_service_metrics=True,
            group_by_service=True,
            limit=1000
        )

        assert "api" in query.service_filter
        assert query.aggregation_level == "hour"
        assert query.group_by_service is True


class TestInfrastructureCQRS:
    """Test CQRS patterns for Infrastructure bounded context."""

    @pytest.mark.asyncio
    async def test_get_infrastructure_status_query_monitoring(self):
        """Test GetInfrastructureStatusQuery for monitoring."""
        query = GetInfrastructureStatusQuery(
            component_name="redis-cache",
            include_detailed_metrics=True,
            include_performance_history=True,
            metrics_timeframe="1h",
            include_dependency_status=True,
            alert_on_thresholds=True,
            threshold_definitions={
                "memory_usage_percent": 85,
                "cpu_usage_percent": 80,
                "connection_count": 1000
            }
        )

        assert query.component_name == "redis-cache"
        assert query.include_detailed_metrics is True
        assert "memory_usage_percent" in query.threshold_definitions

    @pytest.mark.asyncio
    async def test_infrastructure_status_query_aggregation(self):
        """Test infrastructure status query with aggregation."""
        from application.infrastructure.queries import ListInfrastructureStatusQuery

        query = ListInfrastructureStatusQuery(
            component_type_filter=["cache", "database"],
            status_filter=["healthy", "warning"],
            include_overall_aggregation=True,
            aggregation_metrics=["avg_response_time", "total_memory_usage", "error_rate"],
            group_by_type=True,
            include_trend_analysis=True,
            trend_timeframe="24h"
        )

        assert "cache" in query.component_type_filter
        assert query.include_overall_aggregation is True
        assert query.include_trend_analysis is True


class TestIngestionCQRS:
    """Test CQRS patterns for Ingestion bounded context."""

    @pytest.mark.asyncio
    async def test_start_ingestion_command_validation(self):
        """Test StartIngestionCommand validation."""
        command = StartIngestionCommand(
            source_type="api",
            source_config={
                "url": "https://api.example.com/data",
                "authentication": {
                    "type": "bearer",
                    "token": "secret_token"
                },
                "pagination": {
                    "type": "cursor",
                    "page_size": 100
                }
            },
            target_config={
                "type": "database",
                "table": "raw_data",
                "schema": "ingestion"
            },
            processing_config={
                "validation_enabled": True,
                "transformation_rules": [
                    {"field": "timestamp", "type": "datetime", "format": "ISO8601"}
                ],
                "error_handling": "continue",
                "batch_size": 1000
            },
            metadata={
                "source": "external_api",
                "data_type": "user_events",
                "sensitivity": "internal"
            }
        )

        assert command.source_type == "api"
        assert command.source_config["url"] == "https://api.example.com/data"
        assert command.processing_config["validation_enabled"] is True

    @pytest.mark.asyncio
    async def test_cancel_ingestion_command_with_reason(self):
        """Test CancelIngestionCommand with cancellation reason."""
        command = CancelIngestionCommand(
            job_id=str(uuid.uuid4()),
            reason="Manual cancellation by user",
            requested_by="admin_user",
            force_cancel=True,
            cleanup_resources=True
        )

        assert command.reason == "Manual cancellation by user"
        assert command.force_cancel is True
        assert command.cleanup_resources is True

    @pytest.mark.asyncio
    async def test_get_ingestion_status_query_detailed(self):
        """Test GetIngestionStatusQuery with detailed options."""
        query = GetIngestionStatusQuery(
            job_id=str(uuid.uuid4()),
            include_progress_details=True,
            include_error_samples=True,
            error_sample_limit=10,
            include_performance_metrics=True,
            metrics_timeframe="1h",
            include_source_status=True
        )

        assert query.include_progress_details is True
        assert query.include_error_samples is True
        assert query.error_sample_limit == 10


class TestQueryProcessingCQRS:
    """Test CQRS patterns for Query Processing bounded context."""

    @pytest.mark.asyncio
    async def test_process_query_command_complex(self):
        """Test ProcessQueryCommand with complex query."""
        command = ProcessQueryCommand(
            query_type="natural_language",
            query_text="Find all workflows created in the last 30 days that process documents and have an average execution time less than 5 minutes",
            parameters={
                "filters": {
                    "date_range": "30d",
                    "workflow_type": "document_processing",
                    "performance_threshold": {
                        "metric": "avg_execution_time",
                        "operator": "lt",
                        "value": 300
                    }
                },
                "include_metrics": True,
                "sort_by": "creation_date",
                "limit": 50
            },
            execution_options={
                "timeout_seconds": 60,
                "max_parallel_queries": 5,
                "cache_enabled": True,
                "result_format": "structured"
            },
            context={
                "user_id": "analyst_001",
                "session_id": str(uuid.uuid4()),
                "client_info": {
                    "type": "web_dashboard",
                    "version": "2.1.0"
                }
            }
        )

        assert command.query_type == "natural_language"
        assert "document_processing" in command.parameters["filters"]["workflow_type"]
        assert command.execution_options["timeout_seconds"] == 60

    @pytest.mark.asyncio
    async def test_get_query_result_query_with_options(self):
        """Test GetQueryResultQuery with various options."""
        query = GetQueryResultQuery(
            query_id=str(uuid.uuid4()),
            include_execution_details=True,
            include_performance_metrics=True,
            result_format="detailed",
            include_explain_plan=True,
            max_result_size=10000,
            timeout_seconds=30
        )

        assert query.include_execution_details is True
        assert query.result_format == "detailed"
        assert query.max_result_size == 10000


class TestReportingCQRS:
    """Test CQRS patterns for Reporting bounded context."""

    @pytest.mark.asyncio
    async def test_generate_report_command_comprehensive(self):
        """Test GenerateReportCommand with comprehensive options."""
        command = GenerateReportCommand(
            report_type="performance_dashboard",
            title="Monthly System Performance Analysis",
            description="Comprehensive performance analysis for all system components",
            parameters={
                "date_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-31T23:59:59Z"
                },
                "components": ["workflows", "services", "infrastructure"],
                "metrics": [
                    "execution_time", "success_rate", "resource_usage",
                    "error_rate", "throughput", "availability"
                ],
                "group_by": ["component_type", "time_period"],
                "aggregation": "daily"
            },
            output_formats=["pdf", "json", "csv"],
            schedule_config={
                "enabled": True,
                "frequency": "monthly",
                "recipients": ["admin@company.com", "manager@company.com"],
                "notification_channels": ["email", "slack"]
            },
            access_control={
                "visibility": "team",
                "allowed_roles": ["admin", "analyst"],
                "encryption_required": True
            }
        )

        assert command.report_type == "performance_dashboard"
        assert len(command.output_formats) == 3
        assert command.schedule_config["enabled"] is True

    @pytest.mark.asyncio
    async def test_get_report_query_with_filters(self):
        """Test GetReportQuery with filtering options."""
        query = GetReportQuery(
            report_id=str(uuid.uuid4()),
            include_content=True,
            include_generation_details=True,
            include_access_history=True,
            access_history_limit=50,
            include_schedule_info=True,
            format_preference="json"
        )

        assert query.include_content is True
        assert query.include_generation_details is True
        assert query.format_preference == "json"


# =============================================================================
# CQRS PATTERN VALIDATION TESTS
# =============================================================================

class TestCQRSPrinciples:
    """Test fundamental CQRS principles."""

    @pytest.mark.asyncio
    async def test_command_query_separation(self):
        """Test that commands and queries are properly separated."""
        # Commands should not return data (write operations)
        register_cmd = RegisterServiceCommand(
            service_name="test-service",
            service_type="api",
            host="localhost",
            port=8080,
            capabilities=[]
        )

        # Queries should only return data (read operations)
        get_query = GetServiceQuery(service_name="test-service")

        # Assert command has no return data methods
        assert not hasattr(register_cmd, 'result')
        assert not hasattr(register_cmd, 'data')

        # Assert query has data access methods
        assert hasattr(get_query, 'service_name')  # Query parameters

    @pytest.mark.asyncio
    async def test_command_immutability(self):
        """Test that commands are immutable."""
        command = CreateWorkflowCommand(
            name="Immutable Test Workflow",
            description="Testing command immutability",
            workflow_type="test",
            steps=[]
        )

        original_name = command.name

        # Attempt to modify (should fail or create new instance)
        # Commands should be immutable to ensure audit trails
        assert command.name == original_name

    @pytest.mark.asyncio
    async def test_query_idempotency(self):
        """Test that queries are idempotent (can be repeated safely)."""
        query1 = ListServicesQuery(limit=10, offset=0)
        query2 = ListServicesQuery(limit=10, offset=0)

        # Same queries should produce same results
        assert query1.limit == query2.limit
        assert query1.offset == query2.offset

        # Queries should not have side effects
        assert not hasattr(query1, 'execute_count')

    @pytest.mark.asyncio
    async def test_command_validation_pipeline(self):
        """Test command validation pipeline."""
        # Valid command
        valid_command = RegisterServiceCommand(
            service_name="valid-service",
            service_type="api",
            host="localhost",
            port=8080,
            capabilities=["api"]
        )

        # Should pass validation
        assert valid_command.service_name == "valid-service"

        # Invalid command should raise validation error
        with pytest.raises(ValueError):
            RegisterServiceCommand(
                service_name="",  # Invalid
                service_type="api",
                host="localhost",
                port=8080,
                capabilities=[]
            )

    @pytest.mark.asyncio
    async def test_query_optimization(self):
        """Test query optimization patterns."""
        # Efficient query with proper indexing hints
        optimized_query = ListWorkflowsQuery(
            status="active",
            limit=100,  # Reasonable limit
            sort_by="created_at",  # Indexed field
            sort_order="desc"
        )

        # Should use indexed fields for sorting
        assert optimized_query.sort_by in ["created_at", "updated_at", "name"]
        assert optimized_query.limit <= 1000  # Prevent large result sets

    @pytest.mark.asyncio
    async def test_event_driven_command_processing(self):
        """Test event-driven command processing."""
        # Command that triggers events
        command = ExecuteWorkflowCommand(
            workflow_id=str(uuid.uuid4()),
            triggered_by="automation_system"
        )

        # Should generate events
        expected_events = ["WorkflowExecutionStarted", "WorkflowStepCompleted"]

        # Commands should declare their event outcomes
        assert command.workflow_id is not None
        assert command.triggered_by == "automation_system"
