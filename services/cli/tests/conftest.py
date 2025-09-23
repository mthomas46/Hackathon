"""Pytest configuration and shared fixtures for CLI Service tests.

This module provides comprehensive test fixtures for enterprise-grade testing
of command execution, workflow operations, interactive features, and service
coordination within the CLI service.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta
from argparse import Namespace

from modules.models import CommandResult, ServiceStatus, WorkflowExecution


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
def sample_command_result():
    """Sample CommandResult entity."""
    return CommandResult(
        command_id=str(uuid.uuid4()),
        command="status",
        args={"service": "all"},
        status="success",
        output="All services are running",
        error_message=None,
        execution_time_ms=150,
        timestamp=datetime.now(),
        user="test_user",
        session_id=str(uuid.uuid4())
    )


@pytest.fixture
def sample_service_status():
    """Sample ServiceStatus entity."""
    return ServiceStatus(
        service_name="interpreter",
        status="healthy",
        version="1.0.0",
        uptime_seconds=3600,
        response_time_ms=45,
        last_check=datetime.now(),
        endpoint="http://localhost:5005",
        dependencies={
            "llm_gateway": "healthy",
            "orchestrator": "healthy"
        },
        metrics={
            "requests_total": 1250,
            "errors_total": 5,
            "avg_response_time": 42
        }
    )


@pytest.fixture
def sample_workflow_execution():
    """Sample WorkflowExecution entity."""
    return WorkflowExecution(
        workflow_id=str(uuid.uuid4()),
        name="Document Analysis Workflow",
        steps=[
            {
                "step_id": "extract_text",
                "name": "Text Extraction",
                "command": "doc-store extract",
                "args": {"document_id": "doc_123"},
                "status": "completed",
                "execution_time_ms": 250
            },
            {
                "step_id": "analyze_content",
                "name": "Content Analysis",
                "command": "interpreter analyze",
                "args": {"content": "extracted_text"},
                "status": "running",
                "execution_time_ms": 850
            }
        ],
        status="running",
        started_at=datetime.now() - timedelta(minutes=2),
        completed_at=None,
        total_execution_time_ms=1100,
        results={},
        errors=[]
    )


@pytest.fixture
def sample_command_args():
    """Sample command line arguments."""
    return Namespace(
        command="status",
        service="all",
        verbose=True,
        json_output=False,
        timeout=30,
        config_file=None,
        log_level="INFO"
    )


@pytest.fixture
def sample_interactive_session():
    """Sample interactive session data."""
    return {
        "session_id": str(uuid.uuid4()),
        "user": "test_user",
        "start_time": datetime.now(),
        "commands_executed": [
            {"command": "help", "timestamp": datetime.now() - timedelta(minutes=5)},
            {"command": "status", "timestamp": datetime.now() - timedelta(minutes=3)},
            {"command": "workflow list", "timestamp": datetime.now() - timedelta(minutes=1)}
        ],
        "current_context": {
            "working_directory": "/home/user",
            "active_workflow": None,
            "environment": "development"
        },
        "session_state": "active"
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_service_adapter():
    """Mock service adapter for external service communication."""
    mock_adapter = AsyncMock()
    mock_adapter.health_check = AsyncMock(return_value={
        "status": "healthy",
        "response_time_ms": 45,
        "version": "1.0.0"
    })
    mock_adapter.execute_command = AsyncMock(return_value={
        "success": True,
        "result": "Command executed successfully",
        "execution_time_ms": 150
    })
    mock_adapter.get_status = AsyncMock(return_value={
        "status": "running",
        "uptime": 3600,
        "metrics": {"requests": 100, "errors": 2}
    })
    return mock_adapter


@pytest.fixture
def mock_orchestrator_adapter(mock_service_adapter):
    """Mock orchestrator service adapter."""
    mock_orch = AsyncMock()
    mock_orch.execute_workflow = AsyncMock(return_value={
        "workflow_id": str(uuid.uuid4()),
        "status": "running",
        "steps_completed": 2,
        "total_steps": 5
    })
    mock_orch.get_workflow_status = AsyncMock(return_value={
        "status": "completed",
        "execution_time_ms": 2500,
        "results": {"processed_items": 150}
    })
    mock_orch.list_workflows = AsyncMock(return_value=[
        {"id": str(uuid.uuid4()), "name": "Data Processing", "status": "active"},
        {"id": str(uuid.uuid4()), "name": "Analysis Pipeline", "status": "completed"}
    ])
    return mock_orch


@pytest.fixture
def mock_interpreter_adapter(mock_service_adapter):
    """Mock interpreter service adapter."""
    mock_interp = AsyncMock()
    mock_interp.analyze_text = AsyncMock(return_value={
        "analysis": "Document contains technical content about AI",
        "confidence": 0.89,
        "topics": ["artificial intelligence", "technology"]
    })
    mock_interp.process_query = AsyncMock(return_value={
        "response": "Based on the analysis...",
        "processing_time_ms": 1200,
        "tokens_used": 150
    })
    return mock_interp


@pytest.fixture
def mock_doc_store_adapter(mock_service_adapter):
    """Mock document store adapter."""
    mock_doc = AsyncMock()
    mock_doc.store_document = AsyncMock(return_value={"document_id": str(uuid.uuid4())})
    mock_doc.retrieve_document = AsyncMock(return_value={
        "content": "Sample document content",
        "metadata": {"author": "Test Author", "created": "2024-01-01"}
    })
    mock_doc.search_documents = AsyncMock(return_value=[
        {"id": str(uuid.uuid4()), "title": "AI Overview", "relevance": 0.95},
        {"id": str(uuid.uuid4()), "title": "ML Guide", "relevance": 0.87}
    ])
    return mock_doc


@pytest.fixture
def mock_prompt_store_adapter(mock_service_adapter):
    """Mock prompt store adapter."""
    mock_prompt = AsyncMock()
    mock_prompt.get_prompt = AsyncMock(return_value={
        "prompt_id": str(uuid.uuid4()),
        "content": "Analyze the following document...",
        "category": "analysis"
    })
    mock_prompt.list_prompts = AsyncMock(return_value=[
        {"id": str(uuid.uuid4()), "name": "Analysis Prompt", "category": "analysis"},
        {"id": str(uuid.uuid4()), "name": "Summary Prompt", "category": "summarization"}
    ])
    return mock_prompt


@pytest.fixture
def mock_memory_agent_adapter(mock_service_adapter):
    """Mock memory agent adapter."""
    mock_memory = AsyncMock()
    mock_memory.store_memory = AsyncMock(return_value={"memory_id": str(uuid.uuid4())})
    mock_memory.retrieve_memories = AsyncMock(return_value=[
        {"content": "Previous AI discussion", "timestamp": datetime.now(), "relevance": 0.9}
    ])
    mock_memory.search_memories = AsyncMock(return_value=[
        {"id": str(uuid.uuid4()), "content": "AI conversation", "relevance": 0.95}
    ])
    return mock_memory


@pytest.fixture
def mock_command_handler():
    """Mock command handler for CLI operations."""
    mock_handler = MagicMock()
    mock_handler.execute = MagicMock(return_value={
        "success": True,
        "output": "Command executed successfully",
        "execution_time_ms": 150
    })
    mock_handler.validate_args = MagicMock(return_value=True)
    mock_handler.get_help = MagicMock(return_value="Help text for command")
    return mock_handler


@pytest.fixture
def mock_workflow_manager():
    """Mock workflow manager for multi-step operations."""
    mock_wf = AsyncMock()
    mock_wf.create_workflow = AsyncMock(return_value=str(uuid.uuid4()))
    mock_wf.execute_workflow = AsyncMock(return_value={
        "status": "completed",
        "execution_time_ms": 2500,
        "steps_executed": 5,
        "results": {"processed_items": 100}
    })
    mock_wf.get_workflow_status = AsyncMock(return_value={
        "status": "running",
        "progress": 60.0,
        "current_step": "analysis"
    })
    mock_wf.list_workflows = AsyncMock(return_value=[
        {"id": str(uuid.uuid4()), "name": "Data Pipeline", "status": "active"}
    ])
    return mock_wf


@pytest.fixture
def mock_config_manager():
    """Mock configuration manager."""
    mock_config = MagicMock()
    mock_config.get_config = MagicMock(return_value={
        "services": {
            "interpreter": {"url": "http://localhost:5005", "enabled": True},
            "orchestrator": {"url": "http://localhost:5050", "enabled": True}
        },
        "cli": {
            "timeout": 30,
            "verbose": False,
            "output_format": "text"
        }
    })
    mock_config.update_config = MagicMock(return_value=True)
    mock_config.validate_config = MagicMock(return_value=True)
    return mock_config


@pytest.fixture
def mock_formatter():
    """Mock output formatter."""
    mock_fmt = MagicMock()
    mock_fmt.format_output = MagicMock(return_value="Formatted output")
    mock_fmt.format_table = MagicMock(return_value="| Col1 | Col2 |\n|------|------|\n| Val1 | Val2 |")
    mock_fmt.format_status = MagicMock(return_value="✓ Service healthy")
    return mock_fmt


@pytest.fixture
def mock_display_utils():
    """Mock display utilities."""
    mock_display = MagicMock()
    mock_display.print_success = MagicMock()
    mock_display.print_error = MagicMock()
    mock_display.print_warning = MagicMock()
    mock_display.print_info = MagicMock()
    mock_display.show_progress = MagicMock()
    mock_display.clear_screen = MagicMock()
    return mock_display


@pytest.fixture
def mock_interactive_overlay():
    """Mock interactive overlay for CLI interactions."""
    mock_overlay = AsyncMock()
    mock_overlay.start_interactive_session = AsyncMock(return_value=str(uuid.uuid4()))
    mock_overlay.process_command = AsyncMock(return_value={
        "output": "Interactive command result",
        "session_active": True
    })
    mock_overlay.get_command_suggestions = AsyncMock(return_value=[
        "status", "workflow list", "help"
    ])
    mock_overlay.show_help = AsyncMock(return_value="Interactive help displayed")
    return mock_overlay


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return {
        "services": {
            "interpreter": "http://localhost:5005",
            "orchestrator": "http://localhost:5050",
            "doc_store": "http://localhost:5010",
            "prompt_store": "http://localhost:5110",
            "memory_agent": "http://localhost:5040"
        },
        "cli": {
            "timeout": 30,
            "max_retries": 3,
            "output_format": "json",
            "interactive_mode": False
        },
        "test_timeout": 60,
        "cleanup_after_tests": True,
        "test_data": {
            "commands": 50,
            "workflows": 10,
            "sessions": 5
        }
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for integration testing."""
    return {
        "interpreter": AsyncMock(),
        "orchestrator": AsyncMock(),
        "doc_store": AsyncMock(),
        "prompt_store": AsyncMock(),
        "memory_agent": AsyncMock(),
        "log_collector": AsyncMock(),
        "notification_service": AsyncMock()
    }


# =============================================================================
# PERFORMANCE TEST FIXTURES
# =============================================================================

@pytest.fixture
def performance_test_data():
    """Test data for performance benchmarking."""
    return {
        "commands": [
            {
                "command": f"status --service service_{i}",
                "expected_time_ms": 100,
                "complexity": "simple"
            }
            for i in range(100)
        ],
        "workflows": [
            {
                "name": f"Workflow {i}",
                "steps": [
                    "interpreter analyze",
                    "doc-store search",
                    "prompt-store get",
                    f"memory-agent store step_{i}"
                ],
                "expected_duration_ms": 2000
            }
            for i in range(25)
        ],
        "interactive_sessions": [
            {
                "commands": [
                    "help",
                    "status",
                    "workflow list",
                    f"service_{i} health",
                    "exit"
                ],
                "expected_session_time_ms": 5000
            }
            for i in range(10)
        ],
        "concurrent_operations": [
            {
                "operation": "bulk_status_check",
                "concurrent_requests": 20,
                "services": ["interpreter", "orchestrator", "doc_store", "prompt_store"],
                "expected_total_time_ms": 3000
            },
            {
                "operation": "parallel_workflows",
                "concurrent_workflows": 5,
                "workflow_steps": 10,
                "expected_total_time_ms": 15000
            }
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
            "command_execution": {
                "weight": 40,
                "steps": ["parse_command", "validate_args", "execute_command", "format_output"]
            },
            "workflow_operations": {
                "weight": 30,
                "steps": ["create_workflow", "execute_steps", "monitor_progress", "collect_results"]
            },
            "interactive_sessions": {
                "weight": 20,
                "steps": ["start_session", "process_commands", "show_suggestions", "end_session"]
            },
            "service_coordination": {
                "weight": 10,
                "steps": ["health_checks", "status_queries", "bulk_operations", "error_handling"]
            }
        },
        "thresholds": {
            "avg_response_time_ms": 200,
            "error_rate_percent": 1.0,
            "throughput_commands_per_sec": 25,
            "interactive_session_success_rate": 0.95
        }
    }


# =============================================================================
# CHAOS ENGINEERING FIXTURES
# =============================================================================

@pytest.fixture
def chaos_experiment_config():
    """Configuration for chaos engineering experiments."""
    return {
        "experiment_name": "cli_service_resilience_test",
        "duration_minutes": 15,
        "failure_scenarios": [
            {
                "type": "service_unavailable",
                "target": "interpreter",
                "duration_seconds": 120,
                "impact": "high",
                "fallback_test": True
            },
            {
                "type": "network_latency",
                "target": "all_services",
                "latency_ms": 5000,
                "duration_seconds": 180,
                "impact": "medium"
            },
            {
                "type": "command_timeout",
                "target": "workflow_execution",
                "timeout_ms": 1000,
                "duration_seconds": 90,
                "impact": "medium",
                "graceful_degradation_test": True
            },
            {
                "type": "memory_pressure",
                "target": "cli_process",
                "memory_limit_mb": 50,
                "duration_seconds": 300,
                "impact": "high"
            }
        ],
        "monitoring": {
            "metrics": ["command_success_rate", "workflow_completion_rate", "response_time", "error_rate"],
            "alerts": ["command_failure_rate > 10%", "workflow_timeout_rate > 5%", "memory_usage > 90%"],
            "recovery_time_sla": 300
        },
        "data_integrity_checks": [
            "command_history_preservation",
            "workflow_state_consistency",
            "session_data_integrity",
            "configuration_backup"
        ]
    }


@pytest.fixture
def mock_failure_injector():
    """Mock failure injector for chaos testing."""
    mock_injector = MagicMock()
    mock_injector.inject_service_failure = MagicMock(return_value=True)
    mock_injector.inject_network_latency = MagicMock(return_value=True)
    mock_injector.inject_command_timeout = MagicMock(return_value=True)
    mock_injector.inject_memory_pressure = MagicMock(return_value=True)
    mock_injector.restore_normal_operation = MagicMock(return_value=True)
    mock_injector.get_system_health = MagicMock(return_value={
        "status": "degraded",
        "active_failures": ["service_unavailable", "high_memory"],
        "recovery_eta_seconds": 90,
        "command_success_rate": 0.75
    })
    return mock_injector
