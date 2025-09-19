"""Shared test configuration and fixtures for Project Simulation Service.

Provides common test setup, fixtures, and utilities reused across all test layers.
Follows established ecosystem testing patterns for consistency and maintainability.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Add the services path to Python path
services_path = Path(__file__).parent.parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

# Also add the project-simulation path directly
project_sim_path = services_path / "project-simulation"
sys.path.insert(0, str(project_sim_path))

# Create mock shared modules for testing
import types

# Mock services.shared module
shared_mock = types.ModuleType('services.shared')
sys.modules['services.shared'] = shared_mock

# Mock services.shared.core
shared_core = types.ModuleType('services.shared.core')
sys.modules['services.shared.core'] = shared_core

# Mock services.shared.core.responses
shared_responses = types.ModuleType('services.shared.core.responses')
sys.modules['services.shared.core.responses'] = shared_responses

# Mock services.shared.utilities
shared_utilities = types.ModuleType('services.shared.utilities')
sys.modules['services.shared.utilities'] = shared_utilities

# Mock integrations.clients
integrations_mock = types.ModuleType('integrations')
integrations_clients = types.ModuleType('integrations.clients')

# Add ServiceClients class to integrations.clients
class MockServiceClients:
    pass

integrations_clients.ServiceClients = MockServiceClients

sys.modules['integrations'] = integrations_mock
sys.modules['integrations.clients'] = integrations_clients

# Mock utilities.resilience
utilities_mock = types.ModuleType('utilities')
utilities_resilience = types.ModuleType('utilities.resilience')

# Add CircuitBreaker class to utilities.resilience
class MockCircuitBreaker:
    pass

utilities_resilience.CircuitBreaker = MockCircuitBreaker

sys.modules['utilities'] = utilities_mock
sys.modules['utilities.resilience'] = utilities_resilience

# Simple test configuration for integration tests
# We'll mock the app and other dependencies for now

# Define TeamMemberRole for testing if not available
class TeamMemberRole:
    DEVELOPER = "developer"
    QA_ENGINEER = "qa_engineer"
    PRODUCT_OWNER = "product_owner"


# ============================================================================
# SHARED FIXTURES - Reused across test layers
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_project_config() -> Dict[str, Any]:
    """Sample project configuration for testing."""
    return {
        "id": "test_project_001",
        "name": "Test E-commerce Platform",
        "description": "A comprehensive e-commerce platform with microservices architecture",
        "type": "web_application",
        "complexity": "complex",
        "duration_weeks": 12,
        "budget": 250000,
        "technologies": ["Python", "FastAPI", "React", "PostgreSQL", "Redis", "Docker"]
    }


@pytest.fixture
def sample_team_members() -> List[Dict[str, Any]]:
    """Sample team members for testing."""
    return [
        {
            "member_id": "dev_001",
            "name": "Alice Johnson",
            "role": TeamMemberRole.DEVELOPER,
            "experience_years": 5,
            "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
            "productivity_factor": 1.2
        },
        {
            "member_id": "qa_001",
            "name": "Bob Smith",
            "role": TeamMemberRole.QA_ENGINEER,
            "experience_years": 3,
            "skills": ["Selenium", "pytest", "Postman", "Jira"],
            "productivity_factor": 1.0
        },
        {
            "member_id": "pm_001",
            "name": "Carol Williams",
            "role": TeamMemberRole.PRODUCT_OWNER,
            "experience_years": 7,
            "skills": ["Agile", "Scrum", "Product Strategy", "Stakeholder Management"],
            "productivity_factor": 0.9
        }
    ]


@pytest.fixture
def mock_ecosystem_clients():
    """Mock ecosystem service clients for isolated testing."""
    clients = {
        "mock_data_generator": AsyncMock(),
        "analysis_service": AsyncMock(),
        "interpreter": AsyncMock(),
        "doc_store": AsyncMock(),
        "llm_gateway": AsyncMock()
    }

    # Configure common mock responses
    clients["mock_data_generator"].generate_content.return_value = {
        "content": "Mock generated content",
        "metadata": {"quality_score": 0.85}
    }

    clients["analysis_service"].analyze_document_quality.return_value = {
        "overall_score": 0.82,
        "issues": [],
        "recommendations": ["Good documentation quality"]
    }

    clients["interpreter"].generate_insight_content.return_value = {
        "title": "Test Insight",
        "description": "Mock insight content",
        "recommendations": ["Test recommendation"]
    }

    return clients


# ============================================================================
# TEST CONFIGURATION - Environment setup
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "domain: Domain layer tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    import os

    # Set test-specific environment variables
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    yield

    # Cleanup environment variables after all tests
    pass
