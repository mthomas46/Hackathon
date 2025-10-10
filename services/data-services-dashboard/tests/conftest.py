"""
Shared fixtures and configuration for all tests.

Provides fixtures for models, mock data, HTTP mocking, and test utilities.
"""

import pytest
from datetime import datetime, timezone
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock
import httpx

# Test imports
from data.models import LogEntry, MetricsSummary, DashboardFilter
from config import DashboardConfig


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (with dependencies)")
    config.addinivalue_line("markers", "functional: Functional tests (dashboard logic)")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


# ============================================================================
# TIMESTAMP FIXTURES
# ============================================================================

@pytest.fixture
def current_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_timestamp() -> datetime:
    """Get sample timestamp for testing."""
    return datetime(2025, 10, 9, 12, 0, 0, tzinfo=timezone.utc)


# ============================================================================
# DATA MODEL FIXTURES
# ============================================================================

@pytest.fixture
def sample_log_entry(sample_timestamp) -> LogEntry:
    """Create a sample log entry."""
    return LogEntry(
        timestamp=sample_timestamp,
        service="doc_store",
        level="INFO",
        message="Document created successfully",
        operation_type="CREATE",
        method="POST",
        path="/api/v1/documents",
        status_code=201,
        duration_ms=15.5,
        success=True,
        phase="complete",
        workflow_id="wf_abc123"
    )


@pytest.fixture
def failed_log_entry(sample_timestamp) -> LogEntry:
    """Create a failed log entry."""
    return LogEntry(
        timestamp=sample_timestamp,
        service="prompt_store",
        level="ERROR",
        message="Failed to create prompt",
        operation_type="CREATE",
        method="POST",
        path="/api/v1/prompts",
        status_code=500,
        duration_ms=125.5,
        success=False,
        phase="error",
        workflow_id="wf_def456"
    )


@pytest.fixture
def sample_log_entries(sample_log_entry, failed_log_entry) -> List[LogEntry]:
    """Create a list of sample log entries."""
    return [sample_log_entry, failed_log_entry]


@pytest.fixture
def sample_metrics() -> MetricsSummary:
    """Create sample metrics."""
    return MetricsSummary(
        total_operations=100,
        successful_operations=95,
        failed_operations=5,
        avg_duration_ms=12.5,
        error_rate=5.0,
        operations_per_service={
            "doc_store": 50,
            "prompt_store": 30,
            "memory-agent": 20
        }
    )


@pytest.fixture
def sample_dashboard_filter() -> DashboardFilter:
    """Create sample dashboard filter."""
    return DashboardFilter(
        service="doc_store",
        time_range="Last 500 operations",
        operation_type="CREATE"
    )


# ============================================================================
# RAW LOG DATA FIXTURES
# ============================================================================

@pytest.fixture
def raw_log_dict(sample_timestamp) -> Dict[str, Any]:
    """Create raw log dictionary (from log-collector)."""
    return {
        "timestamp": sample_timestamp.isoformat(),
        "service": "doc_store",
        "level": "INFO",
        "message": "Document created successfully",
        "context": {
            "operation_type": "CREATE",
            "method": "POST",
            "path": "/api/v1/documents",
            "status_code": 201,
            "duration_ms": 15.5,
            "success": True,
            "phase": "complete",
            "workflow_id": "wf_abc123"
        }
    }


@pytest.fixture
def raw_log_list(raw_log_dict) -> List[Dict[str, Any]]:
    """Create list of raw log dictionaries."""
    return [raw_log_dict, raw_log_dict.copy()]


@pytest.fixture
def log_collector_response(raw_log_list) -> Dict[str, Any]:
    """Create mock log-collector API response."""
    return {
        "items": raw_log_list,
        "total": len(raw_log_list),
        "limit": 100,
        "service": None
    }


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def test_config() -> DashboardConfig:
    """Create test configuration."""
    return DashboardConfig(
        service_name="data-services-dashboard-test",
        service_version="1.0.0-test",
        ui_port=8501,
        api_port=8080,
        log_collector_url="http://localhost:8104",
        cache_ttl=0,  # Disable caching for tests
        max_retry_attempts=1,  # Minimal retries for faster tests
        retry_delay=0.1,
        http_timeout=1.0
    )


# ============================================================================
# HTTP MOCKING FIXTURES
# ============================================================================

@pytest.fixture
def mock_httpx_client(mocker, log_collector_response):
    """Mock httpx.Client for HTTP requests."""
    mock_client = mocker.MagicMock(spec=httpx.Client)
    mock_response = mocker.MagicMock(spec=httpx.Response)
    
    # Configure response
    mock_response.status_code = 200
    mock_response.json.return_value = log_collector_response
    mock_response.raise_for_status.return_value = None
    
    # Configure client
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_successful_response(mocker, log_collector_response):
    """Mock successful HTTP response."""
    mock_response = mocker.MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = log_collector_response
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_failed_response(mocker):
    """Mock failed HTTP response (500 error)."""
    mock_response = mocker.MagicMock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Internal Server Error",
        request=mocker.MagicMock(),
        response=mock_response
    )
    return mock_response


@pytest.fixture
def mock_timeout_error(mocker):
    """Mock timeout error."""
    return httpx.TimeoutException("Request timeout")


@pytest.fixture
def mock_connection_error(mocker):
    """Mock connection error."""
    return httpx.ConnectError("Connection refused")


# ============================================================================
# FASTAPI TESTING FIXTURES
# ============================================================================

@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient
    from api.router import api_router as router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    
    return TestClient(app)


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def cleanup_cache():
    """Cleanup Streamlit cache after tests."""
    yield
    # Cache cleanup would go here if needed
    pass


@pytest.fixture
def sample_workflow_logs(sample_timestamp) -> List[LogEntry]:
    """Create sample workflow logs."""
    workflow_id = "wf_test_workflow"
    
    logs = []
    for i in range(5):
        log = LogEntry(
            timestamp=sample_timestamp,
            service=f"service_{i % 2}",  # Alternate between 2 services
            level="INFO",
            message=f"Operation {i} in workflow",
            operation_type=["CREATE", "READ", "UPDATE"][i % 3],
            method="POST",
            path=f"/api/v1/resource/{i}",
            status_code=200,
            duration_ms=10.0 + i,
            success=True,
            phase="complete",
            workflow_id=workflow_id
        )
        logs.append(log)
    
    return logs


@pytest.fixture
def sample_services() -> List[str]:
    """Get sample service names."""
    return ["doc_store", "prompt_store", "external-service-store", "memory-agent"]


# ============================================================================
# MOCK LOGGER FIXTURES
# ============================================================================

@pytest.fixture
def mock_logger(mocker):
    """Mock LogCollectorClient to avoid actual HTTP calls."""
    mock = mocker.MagicMock()
    mock.info = mocker.MagicMock()
    mock.warning = mocker.MagicMock()
    mock.error = mocker.MagicMock()
    mock.debug = mocker.MagicMock()
    return mock


@pytest.fixture
def mock_dashboard_logger(mocker):
    """Mock DashboardLogger."""
    mock = mocker.MagicMock()
    mock.dashboard_started = mocker.MagicMock()
    mock.dashboard_stopped = mocker.MagicMock()
    mock.fetching_logs = mocker.MagicMock()
    mock.logs_fetched = mocker.MagicMock()
    mock.fetch_timeout = mocker.MagicMock()
    mock.fetch_failed = mocker.MagicMock()
    return mock

