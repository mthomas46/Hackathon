"""Pytest configuration and shared fixtures for Orchestrator Service tests.

This module provides comprehensive test fixtures for enterprise-grade testing
of DDD patterns, CQRS implementation, event-driven architecture, and workflow orchestration.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta

from domain.health_monitoring.entities import ServiceHealth, HealthStatus
from domain.infrastructure.entities import InfrastructureComponent, ComponentStatus
from domain.ingestion.entities import IngestionJob, JobStatus
from domain.query_processing.entities import QueryRequest, QueryResult
from domain.reporting.entities import Report, ReportStatus
from domain.service_registry.entities import ServiceRegistration, ServiceStatus
from domain.workflow_management.entities import Workflow, WorkflowExecution, ExecutionStatus


# =============================================================================
# SHARED TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def request_id():
    """Generate a unique request ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def correlation_id():
    """Generate a unique correlation ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def test_timestamp():
    """Provide a consistent timestamp for testing."""
    return datetime(2024, 1, 1, 12, 0, 0)


# =============================================================================
# DOMAIN ENTITY FIXTURES
# =============================================================================

@pytest.fixture
def sample_service_registration():
    """Sample service registration entity."""
    return ServiceRegistration(
        id=str(uuid.uuid4()),
        service_name="test-service",
        service_type="api",
        host="localhost",
        port=8080,
        status=ServiceStatus.HEALTHY,
        capabilities=["health_check", "data_processing"],
        metadata={"version": "1.0.0", "environment": "test"},
        registered_at=datetime.now(),
        last_seen=datetime.now(),
        health_check_interval=30
    )


@pytest.fixture
def sample_workflow():
    """Sample workflow entity."""
    return Workflow(
        id=str(uuid.uuid4()),
        name="Test Workflow",
        description="A test workflow for validation",
        type="document_processing",
        steps=[
            {
                "id": "step_1",
                "name": "Data Ingestion",
                "type": "ingestion",
                "config": {"source": "api", "format": "json"}
            },
            {
                "id": "step_2",
                "name": "Data Processing",
                "type": "processing",
                "config": {"processor": "llm_gateway", "model": "gpt-4"}
            }
        ],
        created_by="test_user",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        is_active=True,
        tags=["test", "validation"]
    )


@pytest.fixture
def sample_workflow_execution():
    """Sample workflow execution entity."""
    return WorkflowExecution(
        id=str(uuid.uuid4()),
        workflow_id=str(uuid.uuid4()),
        status=ExecutionStatus.RUNNING,
        started_at=datetime.now(),
        current_step="step_1",
        step_results={
            "step_1": {
                "status": "completed",
                "started_at": datetime.now() - timedelta(minutes=5),
                "completed_at": datetime.now() - timedelta(minutes=3),
                "result": {"processed_items": 150, "success_rate": 0.98}
            }
        },
        context={"user_id": "test_user", "priority": "high"},
        metadata={"environment": "test", "version": "1.0.0"}
    )


@pytest.fixture
def sample_ingestion_job():
    """Sample ingestion job entity."""
    return IngestionJob(
        id=str(uuid.uuid4()),
        source_type="api",
        source_config={"url": "https://api.example.com/data", "format": "json"},
        status=JobStatus.PROCESSING,
        total_items=1000,
        processed_items=750,
        successful_items=720,
        failed_items=30,
        created_at=datetime.now() - timedelta(hours=1),
        started_at=datetime.now() - timedelta(minutes=45),
        updated_at=datetime.now(),
        created_by="test_user",
        metadata={"batch_id": "batch_001", "priority": "medium"}
    )


@pytest.fixture
def sample_query_request():
    """Sample query request entity."""
    return QueryRequest(
        id=str(uuid.uuid4()),
        query_type="natural_language",
        query_text="Find all documents related to AI and machine learning",
        parameters={
            "filters": {"category": "technical", "date_range": "2024-01-01:2024-12-31"},
            "limit": 50,
            "sort_by": "relevance"
        },
        requested_by="test_user",
        requested_at=datetime.now(),
        status="processing",
        context={"session_id": str(uuid.uuid4()), "user_role": "analyst"}
    )


@pytest.fixture
def sample_query_result():
    """Sample query result entity."""
    return QueryResult(
        id=str(uuid.uuid4()),
        query_id=str(uuid.uuid4()),
        status="completed",
        results=[
            {
                "id": "doc_001",
                "title": "AI and Machine Learning Overview",
                "relevance_score": 0.95,
                "metadata": {"category": "technical", "author": "John Doe"}
            },
            {
                "id": "doc_002",
                "title": "Deep Learning Fundamentals",
                "relevance_score": 0.87,
                "metadata": {"category": "technical", "author": "Jane Smith"}
            }
        ],
        total_results=150,
        execution_time_ms=2340,
        created_at=datetime.now(),
        metadata={"engine_version": "2.1.0", "cache_used": False}
    )


@pytest.fixture
def sample_report():
    """Sample report entity."""
    return Report(
        id=str(uuid.uuid4()),
        title="Monthly System Performance Report",
        type="performance",
        status=ReportStatus.GENERATED,
        parameters={
            "date_range": "2024-01-01:2024-01-31",
            "metrics": ["response_time", "throughput", "error_rate"],
            "group_by": "service"
        },
        content={
            "summary": {
                "total_requests": 125000,
                "avg_response_time": 245.6,
                "error_rate": 0.02,
                "services_analyzed": 15
            },
            "charts": [
                {
                    "type": "line",
                    "title": "Response Time Trend",
                    "data": {"dates": ["2024-01-01", "2024-01-15", "2024-01-31"], "values": [250, 240, 235]}
                }
            ]
        },
        generated_by="system",
        generated_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        metadata={"format": "interactive", "version": "1.0"}
    )


@pytest.fixture
def sample_service_health():
    """Sample service health entity."""
    return ServiceHealth(
        id=str(uuid.uuid4()),
        service_name="test-service",
        status=HealthStatus.HEALTHY,
        response_time_ms=145,
        last_check=datetime.now(),
        uptime_percentage=99.8,
        error_count=2,
        warning_count=1,
        details={
            "version": "1.0.0",
            "memory_usage_mb": 512,
            "cpu_usage_percent": 23.4,
            "active_connections": 15
        },
        metadata={"check_type": "comprehensive", "environment": "test"}
    )


@pytest.fixture
def sample_infrastructure_component():
    """Sample infrastructure component entity."""
    return InfrastructureComponent(
        id=str(uuid.uuid4()),
        name="redis-cache",
        type="cache",
        status=ComponentStatus.HEALTHY,
        host="localhost",
        port=6379,
        metrics={
            "memory_used_mb": 256,
            "memory_total_mb": 1024,
            "connections_active": 45,
            "connections_total": 1234,
            "hit_rate_percent": 94.2
        },
        last_check=datetime.now(),
        configuration={
            "max_memory": "1gb",
            "timeout": 300,
            "max_connections": 100
        },
        dependencies=["network", "disk"],
        tags=["cache", "redis", "infrastructure"]
    )


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_service_client():
    """Mock service client for external service interactions."""
    mock_client = AsyncMock()
    mock_client.call_service = AsyncMock(return_value={"status": "success", "data": "mock_response"})
    mock_client.health_check = AsyncMock(return_value=True)
    mock_client.get_service_info = AsyncMock(return_value={"version": "1.0.0", "status": "healthy"})
    return mock_client


@pytest.fixture
def mock_repository():
    """Mock repository for domain entity persistence."""
    mock_repo = AsyncMock()
    mock_repo.save = AsyncMock(return_value=True)
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.list_all = AsyncMock(return_value=[])
    mock_repo.update = AsyncMock(return_value=True)
    mock_repo.delete = AsyncMock(return_value=True)
    return mock_repo


@pytest.fixture
def mock_event_bus():
    """Mock event bus for domain event publishing."""
    mock_bus = AsyncMock()
    mock_bus.publish = AsyncMock(return_value=True)
    mock_bus.subscribe = AsyncMock(return_value=True)
    mock_bus.unsubscribe = AsyncMock(return_value=True)
    return mock_bus


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for caching and messaging."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.publish = AsyncMock(return_value=1)
    mock_redis.subscribe = AsyncMock(return_value=None)
    return mock_redis


@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway client for AI-powered features."""
    mock_llm = AsyncMock()
    mock_llm.generate_insights = AsyncMock(return_value={
        "insights": ["Performance trending upward", "Resource optimization recommended"],
        "confidence": 0.89,
        "model_used": "gpt-4-turbo"
    })
    mock_llm.analyze_text = AsyncMock(return_value={
        "sentiment": "positive",
        "topics": ["technology", "innovation"],
        "complexity": "medium"
    })
    return mock_llm


# =============================================================================
# CQRS COMMAND/QUERY FIXTURES
# =============================================================================

@pytest.fixture
def sample_register_service_command():
    """Sample command for service registration."""
    return {
        "command_type": "RegisterService",
        "service_name": "test-service",
        "service_type": "api",
        "host": "localhost",
        "port": 8080,
        "capabilities": ["health_check", "data_processing"],
        "metadata": {"version": "1.0.0"},
        "correlation_id": str(uuid.uuid4()),
        "timestamp": datetime.now()
    }


@pytest.fixture
def sample_create_workflow_command():
    """Sample command for workflow creation."""
    return {
        "command_type": "CreateWorkflow",
        "workflow_name": "Document Analysis Pipeline",
        "description": "Automated document processing workflow",
        "workflow_type": "document_processing",
        "steps": [
            {
                "name": "Extract Text",
                "type": "extraction",
                "config": {"method": "ocr"}
            },
            {
                "name": "Analyze Content",
                "type": "analysis",
                "config": {"model": "gpt-4", "focus": "sentiment"}
            }
        ],
        "created_by": "test_user",
        "correlation_id": str(uuid.uuid4()),
        "timestamp": datetime.now()
    }


@pytest.fixture
def sample_execute_workflow_command():
    """Sample command for workflow execution."""
    return {
        "command_type": "ExecuteWorkflow",
        "workflow_id": str(uuid.uuid4()),
        "input_data": {"document_url": "https://example.com/doc.pdf"},
        "execution_context": {"priority": "high", "timeout": 300},
        "correlation_id": str(uuid.uuid4()),
        "timestamp": datetime.now()
    }


@pytest.fixture
def sample_get_service_health_query():
    """Sample query for service health information."""
    return {
        "query_type": "GetServiceHealth",
        "service_name": "test-service",
        "include_history": True,
        "time_range": "1h",
        "correlation_id": str(uuid.uuid4()),
        "timestamp": datetime.now()
    }


@pytest.fixture
def sample_list_workflows_query():
    """Sample query for listing workflows."""
    return {
        "query_type": "ListWorkflows",
        "status": "active",
        "type": "document_processing",
        "created_by": "test_user",
        "limit": 50,
        "offset": 0,
        "correlation_id": str(uuid.uuid4()),
        "timestamp": datetime.now()
    }


# =============================================================================
# EVENT FIXTURES
# =============================================================================

@pytest.fixture
def sample_workflow_created_event():
    """Sample domain event for workflow creation."""
    return {
        "event_type": "WorkflowCreated",
        "event_id": str(uuid.uuid4()),
        "aggregate_id": str(uuid.uuid4()),
        "event_data": {
            "workflow_name": "Test Workflow",
            "workflow_type": "document_processing",
            "created_by": "test_user",
            "step_count": 3
        },
        "metadata": {
            "version": "1.0",
            "timestamp": datetime.now(),
            "correlation_id": str(uuid.uuid4()),
            "causation_id": str(uuid.uuid4())
        }
    }


@pytest.fixture
def sample_service_health_changed_event():
    """Sample domain event for service health changes."""
    return {
        "event_type": "ServiceHealthChanged",
        "event_id": str(uuid.uuid4()),
        "aggregate_id": str(uuid.uuid4()),
        "event_data": {
            "service_name": "test-service",
            "previous_status": "healthy",
            "new_status": "warning",
            "response_time_ms": 250,
            "error_message": "Response time above threshold"
        },
        "metadata": {
            "version": "1.0",
            "timestamp": datetime.now(),
            "correlation_id": str(uuid.uuid4())
        }
    }


@pytest.fixture
def sample_workflow_execution_started_event():
    """Sample domain event for workflow execution start."""
    return {
        "event_type": "WorkflowExecutionStarted",
        "event_id": str(uuid.uuid4()),
        "aggregate_id": str(uuid.uuid4()),
        "event_data": {
            "workflow_id": str(uuid.uuid4()),
            "execution_id": str(uuid.uuid4()),
            "triggered_by": "api_request",
            "input_data_size": 1024,
            "estimated_duration": 300
        },
        "metadata": {
            "version": "1.0",
            "timestamp": datetime.now(),
            "correlation_id": str(uuid.uuid4())
        }
    }


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return {
        "redis_host": "localhost",
        "redis_port": 6379,
        "external_services": {
            "llm_gateway": {"url": "http://localhost:5020", "timeout": 30},
            "document_store": {"url": "http://localhost:5010", "timeout": 30},
            "prompt_store": {"url": "http://localhost:5110", "timeout": 30}
        },
        "test_data": {
            "service_count": 5,
            "workflow_count": 10,
            "execution_count": 25
        }
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for integration testing."""
    return {
        "llm_gateway": AsyncMock(),
        "document_store": AsyncMock(),
        "prompt_store": AsyncMock(),
        "memory_agent": AsyncMock(),
        "log_collector": AsyncMock()
    }


# =============================================================================
# PERFORMANCE TEST FIXTURES
# =============================================================================

@pytest.fixture
def performance_test_data():
    """Test data for performance benchmarking."""
    return {
        "workflows": [
            {
                "name": f"Performance Workflow {i}",
                "steps": [
                    {"type": "ingestion", "config": {"items": 1000}},
                    {"type": "processing", "config": {"model": "gpt-4"}},
                    {"type": "storage", "config": {"compression": True}}
                ]
            }
            for i in range(100)
        ],
        "services": [
            {
                "name": f"perf-service-{i}",
                "type": "api",
                "capabilities": ["processing", "storage"]
            }
            for i in range(50)
        ],
        "queries": [
            {
                "type": "complex_aggregation",
                "filters": {"date_range": "30d", "services": 10}
            }
            for _ in range(1000)
        ]
    }


@pytest.fixture
def load_test_scenario():
    """Load testing scenario configuration."""
    return {
        "duration_seconds": 300,
        "concurrent_users": 50,
        "ramp_up_seconds": 60,
        "scenarios": {
            "workflow_execution": {
                "weight": 40,
                "steps": ["create_workflow", "execute_workflow", "monitor_execution"]
            },
            "service_queries": {
                "weight": 30,
                "steps": ["health_check", "service_discovery", "capability_query"]
            },
            "data_ingestion": {
                "weight": 20,
                "steps": ["ingest_data", "validate_ingestion", "query_results"]
            },
            "reporting": {
                "weight": 10,
                "steps": ["generate_report", "export_report", "archive_report"]
            }
        },
        "thresholds": {
            "avg_response_time_ms": 500,
            "error_rate_percent": 1.0,
            "throughput_requests_per_sec": 100
        }
    }


# =============================================================================
# CHAOS ENGINEERING FIXTURES
# =============================================================================

@pytest.fixture
def chaos_experiment_config():
    """Configuration for chaos engineering experiments."""
    return {
        "experiment_name": "service_failure_simulation",
        "duration_minutes": 10,
        "failure_scenarios": [
            {
                "type": "service_down",
                "target": "llm_gateway",
                "duration_seconds": 60,
                "impact": "high"
            },
            {
                "type": "network_latency",
                "target": "redis_cache",
                "latency_ms": 500,
                "duration_seconds": 120,
                "impact": "medium"
            },
            {
                "type": "data_corruption",
                "target": "workflow_state",
                "corruption_rate": 0.05,
                "duration_seconds": 90,
                "impact": "medium"
            }
        ],
        "monitoring": {
            "metrics": ["error_rate", "response_time", "throughput"],
            "alerts": ["error_rate > 5%", "response_time > 2000ms"],
            "recovery_time_sla": 300
        }
    }


@pytest.fixture
def mock_failure_injector():
    """Mock failure injector for chaos testing."""
    mock_injector = MagicMock()
    mock_injector.inject_service_failure = MagicMock(return_value=True)
    mock_injector.inject_network_failure = MagicMock(return_value=True)
    mock_injector.inject_data_corruption = MagicMock(return_value=True)
    mock_injector.restore_normal_operation = MagicMock(return_value=True)
    return mock_injector
