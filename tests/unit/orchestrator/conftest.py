"""Orchestrator Service Test Configuration

Provides shared fixtures and test setup for DDD testing across all bounded contexts.
Follows DRY and KISS principles with reusable test infrastructure.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List, Optional


# Shared fixtures for DDD testing
@pytest.fixture
def mock_repository():
    """Generic mock repository for testing."""
    repo = Mock()
    repo.save.return_value = True
    repo.get.return_value = Mock()
    repo.list.return_value = []
    repo.update.return_value = True
    repo.delete.return_value = True
    return repo


@pytest.fixture
def mock_service():
    """Generic mock domain service for testing."""
    service = Mock()
    service.process.return_value = Mock()
    service.validate.return_value = (True, [])
    return service


@pytest.fixture
def mock_external_client():
    """Generic mock external service client."""
    client = Mock()
    client.call.return_value = {"status": "success", "data": {}}
    client.health_check.return_value = {"status": "healthy"}
    return client


@pytest.fixture
def sample_entity_data():
    """Sample entity data for testing."""
    return {
        "id": "test-id-123",
        "name": "Test Entity",
        "description": "Test description",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_command_data():
    """Sample command data for testing."""
    return {
        "name": "Test Command",
        "description": "Test command description",
        "parameters": {"param1": "value1"},
        "metadata": {"source": "test"}
    }


@pytest.fixture
def sample_query_data():
    """Sample query data for testing."""
    return {
        "filters": {"status": "active"},
        "pagination": {"page": 1, "page_size": 20},
        "sorting": {"field": "created_at", "order": "desc"}
    }


# DDD Architecture Test Helpers
class DDDTestHelper:
    """Helper class for DDD testing patterns."""

    @staticmethod
    def create_mock_use_case_result(success: bool = True, data=None, errors: List[str] = None):
        """Create a mock use case result."""
        from services.orchestrator.shared.domain import DomainResult

        if success:
            return DomainResult.success_result(data or {}, "Operation successful")
        else:
            return DomainResult.failure_result(errors or ["Test error"], "Operation failed")

    @staticmethod
    def assert_domain_result_success(result, expected_data=None):
        """Assert that a domain result is successful."""
        assert result.is_success()
        assert result.errors is None or len(result.errors) == 0
        if expected_data is not None:
            assert result.data == expected_data

    @staticmethod
    def assert_domain_result_failure(result, expected_errors=None):
        """Assert that a domain result is a failure."""
        assert not result.is_success()
        assert result.errors is not None and len(result.errors) > 0
        if expected_errors:
            assert result.errors == expected_errors

    @staticmethod
    def create_mock_async_call(return_value=None, side_effect=None):
        """Create a mock async callable."""
        mock_call = AsyncMock()
        if return_value is not None:
            mock_call.return_value = return_value
        if side_effect is not None:
            mock_call.side_effect = side_effect
        return mock_call


@pytest.fixture
def ddd_helper():
    """DDD testing helper fixture."""
    return DDDTestHelper()


# Test data factories for consistent test data
class TestDataFactory:
    """Factory for creating consistent test data across bounded contexts."""

    @staticmethod
    def create_workflow_data(**overrides):
        """Create sample workflow data."""
        base = {
            "name": "Test Workflow",
            "description": "Test workflow description",
            "created_by": "test_user",
            "tags": ["test", "automation"],
            "parameters": [
                {
                    "name": "input_param",
                    "type": "string",
                    "description": "Input parameter",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "action_1",
                    "name": "Test Action",
                    "service_name": "test_service",
                    "action_type": "api_call",
                    "parameters": {"endpoint": "/test"}
                }
            ]
        }
        base.update(overrides)
        return base

    @staticmethod
    def create_service_data(**overrides):
        """Create sample service data."""
        base = {
            "service_name": "test_service",
            "service_url": "http://localhost:8000",
            "capabilities": ["api_call", "data_processing"],
            "metadata": {"version": "1.0.0", "environment": "test"}
        }
        base.update(overrides)
        return base

    @staticmethod
    def create_ingestion_data(**overrides):
        """Create sample ingestion data."""
        base = {
            "source_url": "https://github.com/test/repo",
            "source_type": "github",
            "parameters": {"include_issues": True, "include_prs": False}
        }
        base.update(overrides)
        return base

    @staticmethod
    def create_query_data(**overrides):
        """Create sample query data."""
        base = {
            "query_text": "find all users with admin role",
            "context": {"domain": "user_management"},
            "max_results": 50
        }
        base.update(overrides)
        return base

    @staticmethod
    def create_report_data(**overrides):
        """Create sample report data."""
        base = {
            "report_type": "analytics",
            "parameters": {"time_range": "30d", "metrics": ["usage", "performance"]},
            "format": "json"
        }
        base.update(overrides)
        return base


@pytest.fixture
def test_data_factory():
    """Test data factory fixture."""
    return TestDataFactory()


# Performance testing helpers
@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time
    start_time = None

    def start():
        nonlocal start_time
        start_time = time.time()

    def stop():
        nonlocal start_time
        if start_time is None:
            return 0
        elapsed = time.time() - start_time
        start_time = None
        return elapsed

    return {"start": start, "stop": stop}
