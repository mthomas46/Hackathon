"""Shared test configuration and fixtures for Project Simulation Service.

Provides common test setup, fixtures, and utilities reused across all test layers.
Follows established ecosystem testing patterns for consistency and maintainability.
"""

import pytest
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from services.project_simulation.main import app
from services.project_simulation.simulation.infrastructure.di_container import get_simulation_container
from services.project_simulation.simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, TeamMemberRole, ProjectStatus
)
from services.project_simulation.simulation.content.context_aware_generation import ContentContext


# ============================================================================
# SHARED FIXTURES - Reused across test layers
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_container():
    """Get the simulation container for testing."""
    container = get_simulation_container()
    yield container


@pytest.fixture(scope="function")
async def test_client() -> AsyncGenerator[TestClient, None]:
    """Create a test client for FastAPI application."""
    async with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
async def async_test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for comprehensive API testing."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def sample_project_config() -> Dict[str, Any]:
    """Sample project configuration for testing."""
    return {
        "id": "test_project_001",
        "name": "Test E-commerce Platform",
        "description": "A comprehensive e-commerce platform with microservices architecture",
        "type": ProjectType.WEB_APPLICATION.value,
        "complexity": ComplexityLevel.COMPLEX.value,
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
            "role": TeamMemberRole.DEVELOPER.value,
            "experience_years": 5,
            "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
            "productivity_factor": 1.2
        },
        {
            "member_id": "qa_001",
            "name": "Bob Smith",
            "role": TeamMemberRole.QA_ENGINEER.value,
            "experience_years": 3,
            "skills": ["Selenium", "pytest", "Postman", "Jira"],
            "productivity_factor": 1.0
        },
        {
            "member_id": "pm_001",
            "name": "Carol Williams",
            "role": TeamMemberRole.PRODUCT_OWNER.value,
            "experience_years": 7,
            "skills": ["Agile", "Scrum", "Product Strategy", "Stakeholder Management"],
            "productivity_factor": 0.9
        }
    ]


@pytest.fixture
def sample_timeline() -> Dict[str, Any]:
    """Sample project timeline for testing."""
    return {
        "phases": [
            {
                "name": "Planning",
                "start_date": "2024-01-01",
                "end_date": "2024-01-15",
                "duration_days": 15,
                "status": "completed"
            },
            {
                "name": "Design",
                "start_date": "2024-01-16",
                "end_date": "2024-02-15",
                "duration_days": 30,
                "status": "completed"
            },
            {
                "name": "Development",
                "start_date": "2024-02-16",
                "end_date": "2024-05-15",
                "duration_days": 90,
                "status": "in_progress"
            },
            {
                "name": "Testing",
                "start_date": "2024-05-16",
                "end_date": "2024-06-15",
                "duration_days": 30,
                "status": "pending"
            },
            {
                "name": "Deployment",
                "start_date": "2024-06-16",
                "end_date": "2024-07-01",
                "duration_days": 15,
                "status": "pending"
            }
        ]
    }


@pytest.fixture
def sample_content_context(sample_project_config, sample_team_members, sample_timeline) -> ContentContext:
    """Create a sample content context for testing."""
    return ContentContext(
        project_config=sample_project_config,
        team_members=sample_team_members,
        timeline=sample_timeline
    )


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


@pytest.fixture
def mock_service_dependencies(mock_ecosystem_clients):
    """Mock all service dependencies for unit testing."""
    return {
        "ecosystem_clients": mock_ecosystem_clients,
        "cache": MagicMock(),
        "logger": MagicMock(),
        "validator": MagicMock(),
        "monitoring": MagicMock()
    }


# ============================================================================
# TEST UTILITIES - Reusable test helper functions
# ============================================================================

class TestDataBuilder:
    """Builder pattern for creating test data."""

    def __init__(self):
        self.data = {}

    def with_project(self, **kwargs) -> 'TestDataBuilder':
        """Add project configuration."""
        default_project = {
            "id": f"test_project_{len(self.data)}",
            "name": "Test Project",
            "type": ProjectType.WEB_APPLICATION.value,
            "complexity": ComplexityLevel.MEDIUM.value,
            "duration_weeks": 8
        }
        default_project.update(kwargs)
        self.data["project"] = default_project
        return self

    def with_team(self, size: int = 3) -> 'TestDataBuilder':
        """Add team members."""
        team = []
        roles = [TeamMemberRole.DEVELOPER, TeamMemberRole.QA_ENGINEER, TeamMemberRole.PRODUCT_OWNER]

        for i in range(size):
            team.append({
                "member_id": f"member_{i+1}",
                "name": f"Team Member {i+1}",
                "role": roles[i % len(roles)].value,
                "experience_years": 3 + i,
                "skills": ["Python", "Testing", "Agile"][:i+1]
            })

        self.data["team"] = team
        return self

    def with_timeline(self, phases: int = 4) -> 'TestDataBuilder':
        """Add project timeline."""
        timeline = {"phases": []}

        phase_names = ["Planning", "Design", "Development", "Testing", "Deployment"]
        start_date = "2024-01-01"

        for i in range(min(phases, len(phase_names))):
            timeline["phases"].append({
                "name": phase_names[i],
                "start_date": start_date,
                "end_date": f"2024-01-{15 + i*15:02d}",
                "duration_days": 15,
                "status": "pending"
            })

        self.data["timeline"] = timeline
        return self

    def build(self) -> Dict[str, Any]:
        """Build the complete test data."""
        return self.data


@pytest.fixture
def test_data_builder() -> TestDataBuilder:
    """Provide test data builder fixture."""
    return TestDataBuilder()


class AsyncTestHelper:
    """Helper for async testing operations."""

    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
        """Wait for a condition to become true."""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(interval)

        raise TimeoutError(f"Condition not met within {timeout} seconds")

    @staticmethod
    async def collect_async_results(tasks: List[asyncio.Task]) -> List[Any]:
        """Collect results from multiple async tasks."""
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)
        return results


@pytest.fixture
def async_helper() -> AsyncTestHelper:
    """Provide async test helper fixture."""
    return AsyncTestHelper()


# ============================================================================
# MOCKING UTILITIES - Consistent mocking patterns
# ============================================================================

class MockBuilder:
    """Builder for creating consistent mocks."""

    def __init__(self):
        self.mocks = {}

    def mock_service_client(self, service_name: str) -> 'MockBuilder':
        """Create a mock service client."""
        mock_client = AsyncMock()
        mock_client.service_name = service_name

        # Add common mock methods
        mock_client.generate_content = AsyncMock(return_value={"content": "Mock content"})
        mock_client.analyze_quality = AsyncMock(return_value={"score": 0.8})
        mock_client.get_status = AsyncMock(return_value={"status": "healthy"})

        self.mocks[service_name] = mock_client
        return self

    def mock_repository(self, repo_name: str) -> 'MockBuilder':
        """Create a mock repository."""
        mock_repo = MagicMock()
        mock_repo.name = repo_name
        mock_repo.save = MagicMock(return_value=True)
        mock_repo.get = MagicMock(return_value={"id": "test_id"})
        mock_repo.list = MagicMock(return_value=[])
        mock_repo.delete = MagicMock(return_value=True)

        self.mocks[repo_name] = mock_repo
        return self

    def build(self) -> Dict[str, Any]:
        """Build all mocks."""
        return self.mocks


@pytest.fixture
def mock_builder() -> MockBuilder:
    """Provide mock builder fixture."""
    return MockBuilder()


# ============================================================================
# ASSERTION HELPERS - Common test assertions
# ============================================================================

class TestAssertions:
    """Common test assertion helpers."""

    @staticmethod
    def assert_response_structure(response: Dict[str, Any], required_fields: List[str]):
        """Assert that response has required structure."""
        for field in required_fields:
            assert field in response, f"Required field '{field}' missing from response"

    @staticmethod
    def assert_hypermedia_links(response: Dict[str, Any]):
        """Assert that response includes proper hypermedia links."""
        assert "_links" in response, "Response missing hypermedia links"
        links = response["_links"]
        assert isinstance(links, list), "Links should be a list"
        assert len(links) > 0, "Response should include at least one link"

        # Check for self link
        self_links = [link for link in links if link.get("rel") == "self"]
        assert len(self_links) > 0, "Response should include self link"

    @staticmethod
    def assert_simulation_status(simulation: Dict[str, Any], expected_status: str):
        """Assert simulation has expected status."""
        assert simulation["status"] == expected_status, f"Expected status {expected_status}, got {simulation['status']}"

    @staticmethod
    def assert_content_quality(content: Dict[str, Any], min_score: float = 0.7):
        """Assert content meets quality standards."""
        assert "quality_score" in content, "Content missing quality score"
        assert content["quality_score"] >= min_score, f"Content quality {content['quality_score']} below minimum {min_score}"


@pytest.fixture
def assertions() -> TestAssertions:
    """Provide test assertions fixture."""
    return TestAssertions()


# ============================================================================
# PERFORMANCE TESTING UTILITIES
# ============================================================================

class PerformanceTestHelper:
    """Helper for performance testing."""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start_timer(self):
        """Start performance timer."""
        self.start_time = asyncio.get_event_loop().time()

    def stop_timer(self) -> float:
        """Stop performance timer and return elapsed time."""
        self.end_time = asyncio.get_event_loop().time()
        return self.end_time - self.start_time

    def assert_performance(self, elapsed_time: float, max_time: float, operation: str):
        """Assert that operation completed within time limit."""
        assert elapsed_time <= max_time, f"{operation} took {elapsed_time:.2f}s, exceeded limit of {max_time:.2f}s"


@pytest.fixture
def perf_helper() -> PerformanceTestHelper:
    """Provide performance testing helper fixture."""
    return PerformanceTestHelper()


# ============================================================================
# CLEANUP UTILITIES - Test cleanup helpers
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Automatic cleanup after each test."""
    # This runs after each test
    yield

    # Cleanup logic here
    # For example: clean up test databases, reset mocks, etc.
    pass


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
