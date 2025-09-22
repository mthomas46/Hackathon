"""Unit Tests for DDD Entities in Orchestrator Service.

This module tests domain entities across all bounded contexts:
- Service Registry entities
- Workflow Management entities
- Health Monitoring entities
- Infrastructure entities
- Ingestion entities
- Query Processing entities
- Reporting entities

Tests cover entity creation, validation, business rules, and invariants.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from domain.service_registry.entities import ServiceRegistration, ServiceStatus
from domain.workflow_management.entities import Workflow, WorkflowExecution, ExecutionStatus
from domain.health_monitoring.entities import ServiceHealth, HealthStatus
from domain.infrastructure.entities import InfrastructureComponent, ComponentStatus
from domain.ingestion.entities import IngestionJob, JobStatus
from domain.query_processing.entities import QueryRequest, QueryResult
from domain.reporting.entities import Report, ReportStatus


class TestServiceRegistrationEntity:
    """Test Service Registration domain entity."""

    def test_create_valid_service_registration(self, sample_service_registration):
        """Test creating a valid service registration."""
        registration = sample_service_registration

        assert registration.id is not None
        assert registration.service_name == "test-service"
        assert registration.status == ServiceStatus.HEALTHY
        assert len(registration.capabilities) > 0
        assert registration.registered_at <= datetime.now()

    def test_service_registration_validation(self):
        """Test service registration validation rules."""
        # Test invalid service name
        with pytest.raises(ValueError):
            ServiceRegistration(
                id=str(uuid.uuid4()),
                service_name="",  # Invalid: empty name
                service_type="api",
                host="localhost",
                port=8080,
                status=ServiceStatus.HEALTHY,
                capabilities=[],
                registered_at=datetime.now()
            )

        # Test invalid port
        with pytest.raises(ValueError):
            ServiceRegistration(
                id=str(uuid.uuid4()),
                service_name="test-service",
                service_type="api",
                host="localhost",
                port=70000,  # Invalid: port too high
                status=ServiceStatus.HEALTHY,
                capabilities=[],
                registered_at=datetime.now()
            )

    def test_service_registration_business_rules(self, sample_service_registration):
        """Test business rules for service registration."""
        registration = sample_service_registration

        # Test health check interval bounds
        assert registration.health_check_interval >= 10
        assert registration.health_check_interval <= 300

        # Test capability validation
        assert "health_check" in registration.capabilities

        # Test status transitions
        assert registration.status in [ServiceStatus.HEALTHY, ServiceStatus.UNHEALTHY, ServiceStatus.UNKNOWN]

    def test_service_registration_equality(self):
        """Test entity equality based on ID."""
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())

        reg1 = ServiceRegistration(
            id=id1,
            service_name="service-a",
            service_type="api",
            host="localhost",
            port=8080,
            status=ServiceStatus.HEALTHY,
            capabilities=["api"],
            registered_at=datetime.now()
        )

        reg2 = ServiceRegistration(
            id=id1,  # Same ID
            service_name="service-b",  # Different name
            service_type="worker",
            host="remote",
            port=9090,
            status=ServiceStatus.UNHEALTHY,
            capabilities=["worker"],
            registered_at=datetime.now()
        )

        reg3 = ServiceRegistration(
            id=id2,  # Different ID
            service_name="service-a",  # Same name
            service_type="api",
            host="localhost",
            port=8080,
            status=ServiceStatus.HEALTHY,
            capabilities=["api"],
            registered_at=datetime.now()
        )

        assert reg1 == reg2  # Same ID
        assert reg1 != reg3  # Different ID


class TestWorkflowEntity:
    """Test Workflow domain entity."""

    def test_create_valid_workflow(self, sample_workflow):
        """Test creating a valid workflow."""
        workflow = sample_workflow

        assert workflow.id is not None
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) > 0
        assert workflow.is_active is True
        assert workflow.created_at <= datetime.now()

    def test_workflow_validation(self):
        """Test workflow validation rules."""
        # Test invalid workflow name
        with pytest.raises(ValueError):
            Workflow(
                id=str(uuid.uuid4()),
                name="",  # Invalid: empty name
                description="Test workflow",
                type="processing",
                steps=[],
                created_by="user",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )

        # Test invalid step configuration
        with pytest.raises(ValueError):
            Workflow(
                id=str(uuid.uuid4()),
                name="Test Workflow",
                description="Test workflow",
                type="processing",
                steps=[
                    {
                        "id": "step_1",
                        "name": "",  # Invalid: empty step name
                        "type": "processing",
                        "config": {}
                    }
                ],
                created_by="user",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )

    def test_workflow_business_rules(self, sample_workflow):
        """Test business rules for workflows."""
        workflow = sample_workflow

        # Test step dependencies
        step_ids = [step["id"] for step in workflow.steps]
        assert len(set(step_ids)) == len(step_ids), "Step IDs must be unique"

        # Test workflow type constraints
        valid_types = ["document_processing", "data_analysis", "api_orchestration", "batch_processing"]
        assert workflow.type in valid_types

        # Test tag validation
        assert isinstance(workflow.tags, list)
        assert all(isinstance(tag, str) for tag in workflow.tags)

    def test_workflow_step_execution_order(self, sample_workflow):
        """Test workflow step execution ordering."""
        workflow = sample_workflow

        # Verify step dependencies are respected
        for i, step in enumerate(workflow.steps):
            if i > 0:
                # Each step should have access to previous step outputs
                assert "depends_on" not in step or step["depends_on"] in [
                    s["id"] for s in workflow.steps[:i]
                ]


class TestWorkflowExecutionEntity:
    """Test Workflow Execution domain entity."""

    def test_create_valid_execution(self, sample_workflow_execution):
        """Test creating a valid workflow execution."""
        execution = sample_workflow_execution

        assert execution.id is not None
        assert execution.workflow_id is not None
        assert execution.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]
        assert execution.started_at <= datetime.now()

    def test_execution_state_transitions(self):
        """Test valid execution state transitions."""
        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            workflow_id=str(uuid.uuid4()),
            status=ExecutionStatus.PENDING,
            started_at=datetime.now()
        )

        # Valid transitions
        execution.status = ExecutionStatus.RUNNING
        assert execution.status == ExecutionStatus.RUNNING

        execution.status = ExecutionStatus.COMPLETED
        assert execution.status == ExecutionStatus.COMPLETED

        # Invalid transition (can't go back to running from completed)
        with pytest.raises(ValueError):
            execution.status = ExecutionStatus.RUNNING

    def test_execution_step_progress_tracking(self, sample_workflow_execution):
        """Test execution step progress tracking."""
        execution = sample_workflow_execution

        # Test step results structure
        for step_id, result in execution.step_results.items():
            assert "status" in result
            assert result["status"] in ["pending", "running", "completed", "failed"]
            assert "started_at" in result

            if result["status"] == "completed":
                assert "completed_at" in result
                assert result["completed_at"] > result["started_at"]

    def test_execution_context_preservation(self, sample_workflow_execution):
        """Test execution context preservation."""
        execution = sample_workflow_execution

        # Test context contains required fields
        assert "user_id" in execution.context

        # Test metadata preservation
        assert "environment" in execution.metadata
        assert "version" in execution.metadata


class TestServiceHealthEntity:
    """Test Service Health domain entity."""

    def test_create_valid_health_record(self, sample_service_health):
        """Test creating a valid service health record."""
        health = sample_service_health

        assert health.service_name is not None
        assert health.status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.ERROR]
        assert health.response_time_ms >= 0
        assert 0 <= health.uptime_percentage <= 100

    def test_health_status_calculation(self):
        """Test health status calculation based on metrics."""
        # Healthy service
        healthy = ServiceHealth(
            id=str(uuid.uuid4()),
            service_name="healthy-service",
            status=HealthStatus.HEALTHY,
            response_time_ms=145,
            last_check=datetime.now(),
            uptime_percentage=99.8,
            error_count=0,
            warning_count=1
        )

        assert healthy.status == HealthStatus.HEALTHY

        # Warning service (high response time)
        warning = ServiceHealth(
            id=str(uuid.uuid4()),
            service_name="slow-service",
            status=HealthStatus.WARNING,
            response_time_ms=2500,  # High response time
            last_check=datetime.now(),
            uptime_percentage=95.0,
            error_count=5,
            warning_count=10
        )

        assert warning.status == HealthStatus.WARNING

    def test_health_metrics_validation(self, sample_service_health):
        """Test health metrics validation."""
        health = sample_service_health

        # Test uptime percentage bounds
        assert 0 <= health.uptime_percentage <= 100

        # Test error/warning counts are non-negative
        assert health.error_count >= 0
        assert health.warning_count >= 0

        # Test response time is reasonable
        assert health.response_time_ms >= 0
        assert health.response_time_ms < 30000  # Less than 30 seconds


class TestInfrastructureComponentEntity:
    """Test Infrastructure Component domain entity."""

    def test_create_valid_component(self, sample_infrastructure_component):
        """Test creating a valid infrastructure component."""
        component = sample_infrastructure_component

        assert component.name is not None
        assert component.type in ["cache", "database", "message_queue", "load_balancer", "api_gateway"]
        assert component.status in [ComponentStatus.HEALTHY, ComponentStatus.WARNING, ComponentStatus.ERROR]
        assert component.port > 0 and component.port < 65536

    def test_component_dependency_validation(self, sample_infrastructure_component):
        """Test component dependency validation."""
        component = sample_infrastructure_component

        # Test dependencies are valid component types
        valid_dependency_types = ["network", "disk", "memory", "cpu", "storage"]
        for dep in component.dependencies:
            assert dep in valid_dependency_types

    def test_component_metrics_calculation(self, sample_infrastructure_component):
        """Test component metrics calculation."""
        component = sample_infrastructure_component

        # Test cache hit rate calculation
        if "hit_rate_percent" in component.metrics:
            assert 0 <= component.metrics["hit_rate_percent"] <= 100

        # Test memory usage percentage
        if "memory_used_mb" in component.metrics and "memory_total_mb" in component.metrics:
            usage_percent = (component.metrics["memory_used_mb"] / component.metrics["memory_total_mb"]) * 100
            assert 0 <= usage_percent <= 100


class TestIngestionJobEntity:
    """Test Ingestion Job domain entity."""

    def test_create_valid_ingestion_job(self, sample_ingestion_job):
        """Test creating a valid ingestion job."""
        job = sample_ingestion_job

        assert job.id is not None
        assert job.status in [JobStatus.PENDING, JobStatus.PROCESSING, JobStatus.COMPLETED, JobStatus.FAILED]
        assert job.total_items > 0
        assert job.processed_items <= job.total_items

    def test_ingestion_job_progress_calculation(self, sample_ingestion_job):
        """Test ingestion job progress calculation."""
        job = sample_ingestion_job

        # Test progress percentage
        progress = (job.processed_items / job.total_items) * 100
        assert 0 <= progress <= 100

        # Test success rate
        if job.processed_items > 0:
            success_rate = (job.successful_items / job.processed_items) * 100
            assert 0 <= success_rate <= 100

    def test_ingestion_job_status_transitions(self):
        """Test valid ingestion job status transitions."""
        job = IngestionJob(
            id=str(uuid.uuid4()),
            source_type="api",
            source_config={"url": "https://api.example.com"},
            status=JobStatus.PENDING,
            total_items=100,
            created_at=datetime.now()
        )

        # Valid transitions
        job.status = JobStatus.PROCESSING
        assert job.status == JobStatus.PROCESSING

        job.status = JobStatus.COMPLETED
        assert job.status == JobStatus.COMPLETED

        # Test final state validation
        with pytest.raises(ValueError):
            job.status = JobStatus.PROCESSING  # Can't go back from completed


class TestQueryRequestEntity:
    """Test Query Request domain entity."""

    def test_create_valid_query_request(self, sample_query_request):
        """Test creating a valid query request."""
        request = sample_query_request

        assert request.id is not None
        assert request.query_type in ["natural_language", "structured", "sql", "graph"]
        assert len(request.query_text) > 0
        assert request.requested_by is not None

    def test_query_request_parameter_validation(self, sample_query_request):
        """Test query request parameter validation."""
        request = sample_query_request

        # Test filter parameters
        if "filters" in request.parameters:
            filters = request.parameters["filters"]
            assert isinstance(filters, dict)

            # Test date range format
            if "date_range" in filters:
                date_range = filters["date_range"]
                assert ":" in date_range  # Should contain separator

        # Test limit bounds
        if "limit" in request.parameters:
            limit = request.parameters["limit"]
            assert 1 <= limit <= 1000

    def test_query_context_preservation(self, sample_query_request):
        """Test query context preservation."""
        request = sample_query_request

        # Test session tracking
        assert "session_id" in request.context

        # Test user role tracking
        assert "user_role" in request.context
        assert request.context["user_role"] in ["admin", "analyst", "user", "guest"]


class TestQueryResultEntity:
    """Test Query Result domain entity."""

    def test_create_valid_query_result(self, sample_query_result):
        """Test creating a valid query result."""
        result = sample_query_result

        assert result.id is not None
        assert result.query_id is not None
        assert result.status in ["processing", "completed", "failed", "timeout"]
        assert result.execution_time_ms >= 0

    def test_query_result_scoring(self, sample_query_result):
        """Test query result relevance scoring."""
        result = sample_query_result

        # Test result scoring bounds
        for item in result.results:
            if "relevance_score" in item:
                score = item["relevance_score"]
                assert 0.0 <= score <= 1.0

    def test_query_result_pagination(self, sample_query_result):
        """Test query result pagination."""
        result = sample_query_result

        # Test result count vs total
        assert len(result.results) <= result.total_results

        # Test reasonable execution time
        assert result.execution_time_ms < 300000  # Less than 5 minutes


class TestReportEntity:
    """Test Report domain entity."""

    def test_create_valid_report(self, sample_report):
        """Test creating a valid report."""
        report = sample_report

        assert report.id is not None
        assert report.title is not None
        assert report.type in ["performance", "usage", "error", "security", "compliance"]
        assert report.status in [ReportStatus.PENDING, ReportStatus.GENERATING, ReportStatus.GENERATED, ReportStatus.FAILED]

    def test_report_content_validation(self, sample_report):
        """Test report content validation."""
        report = sample_report

        # Test summary structure
        assert "summary" in report.content
        summary = report.content["summary"]
        assert isinstance(summary, dict)

        # Test charts structure
        if "charts" in report.content:
            charts = report.content["charts"]
            assert isinstance(charts, list)

            for chart in charts:
                assert "type" in chart
                assert "title" in chart
                assert "data" in chart

    def test_report_expiration_logic(self, sample_report):
        """Test report expiration logic."""
        report = sample_report

        # Test expiration date is in the future
        assert report.expires_at > datetime.now()

        # Test reasonable expiration period (not too long)
        expiration_period = report.expires_at - report.generated_at
        assert expiration_period.days <= 365  # Max 1 year


# =============================================================================
# DOMAIN INVARIANT TESTS
# =============================================================================

class TestDomainInvariants:
    """Test domain invariants across entities."""

    def test_entity_id_uniqueness(self):
        """Test that entity IDs are unique across instances."""
        ids = set()

        # Create multiple entities
        entities = [
            ServiceRegistration(id=str(uuid.uuid4()), service_name=f"service_{i}", service_type="api",
                              host="localhost", port=8080+i, status=ServiceStatus.HEALTHY, capabilities=[],
                              registered_at=datetime.now())
            for i in range(10)
        ]

        # Check all IDs are unique
        for entity in entities:
            assert entity.id not in ids
            ids.add(entity.id)

    def test_temporal_consistency(self):
        """Test temporal consistency across related entities."""
        base_time = datetime.now()

        # Create workflow
        workflow = Workflow(
            id=str(uuid.uuid4()),
            name="Temporal Test Workflow",
            description="Testing temporal consistency",
            type="processing",
            steps=[{"id": "step_1", "name": "Process", "type": "processing", "config": {}}],
            created_by="test_user",
            created_at=base_time,
            updated_at=base_time,
            is_active=True
        )

        # Create execution
        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            status=ExecutionStatus.RUNNING,
            started_at=base_time + timedelta(minutes=5)  # Started after workflow creation
        )

        # Assert temporal ordering
        assert execution.started_at >= workflow.created_at

    def test_business_rule_consistency(self):
        """Test business rule consistency across entities."""
        # Create healthy service
        service = ServiceRegistration(
            id=str(uuid.uuid4()),
            service_name="consistent-service",
            service_type="api",
            host="localhost",
            port=8080,
            status=ServiceStatus.HEALTHY,
            capabilities=["health_check", "api"],
            registered_at=datetime.now()
        )

        # Create corresponding health record
        health = ServiceHealth(
            id=str(uuid.uuid4()),
            service_name=service.service_name,  # Same name
            status=HealthStatus.HEALTHY,  # Consistent status
            response_time_ms=145,
            last_check=datetime.now(),
            uptime_percentage=99.8,
            error_count=0,
            warning_count=1
        )

        # Assert consistency
        assert service.service_name == health.service_name
        assert service.status.name.lower() == health.status.value.lower()

    def test_aggregate_boundary_consistency(self):
        """Test consistency within aggregate boundaries."""
        workflow_id = str(uuid.uuid4())

        # Create workflow aggregate root
        workflow = Workflow(
            id=workflow_id,
            name="Aggregate Test Workflow",
            description="Testing aggregate boundaries",
            type="processing",
            steps=[
                {"id": "step_1", "name": "Start", "type": "init", "config": {}},
                {"id": "step_2", "name": "Process", "type": "processing", "config": {}},
                {"id": "step_3", "name": "Finish", "type": "completion", "config": {}}
            ],
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )

        # Create execution within same aggregate
        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,  # References aggregate root
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
            current_step="step_2",  # Valid step from workflow
            step_results={}
        )

        # Assert aggregate consistency
        assert execution.workflow_id == workflow.id
        assert execution.current_step in [step["id"] for step in workflow.steps]
