"""
Pytest configuration and shared fixtures for expert-finder-service tests.
"""

import pytest
from typing import Dict, Any, List
from faker import Faker

fake = Faker()


# ============================================================================
# Domain Fixtures
# ============================================================================

@pytest.fixture
def sample_expert_data() -> Dict[str, Any]:
    """Sample expert data for testing."""
    return {
        "user_id": fake.uuid4(),
        "name": fake.name(),
        "role": "Backend Developer",
        "seniority": "senior",
        "topics": ["Python", "FastAPI", "Docker", "Microservices"],
        "tags": ["backend", "python", "api"],
        "services": ["user-store", "doc-store"],
        "created_at": fake.iso8601()
    }


@pytest.fixture
def sample_expert_list() -> List[Dict[str, Any]]:
    """List of sample experts for testing."""
    return [
        {
            "user_id": fake.uuid4(),
            "name": "Alice Smith",
            "role": "Backend Developer",
            "seniority": "senior",
            "topics": ["Python", "FastAPI", "Docker"],
            "tags": ["backend", "python"],
            "services": ["user-store"],
        },
        {
            "user_id": fake.uuid4(),
            "name": "Bob Johnson",
            "role": "Frontend Developer",
            "seniority": "mid",
            "topics": ["React", "TypeScript", "CSS"],
            "tags": ["frontend", "react"],
            "services": ["ui-service"],
        },
        {
            "user_id": fake.uuid4(),
            "name": "Carol Williams",
            "role": "Full Stack Developer",
            "seniority": "senior",
            "topics": ["Python", "React", "PostgreSQL"],
            "tags": ["fullstack", "database"],
            "services": ["user-store", "ui-service"],
        },
    ]


@pytest.fixture
def sample_query_data() -> Dict[str, Any]:
    """Sample query data for testing."""
    return {
        "query_text": "Python backend developer",
        "role": "Backend Developer",
        "topics": ["Python", "FastAPI"],
        "services": ["user-store"],
        "limit": 10
    }


# ============================================================================
# Repository Fixtures (Mocked External Services)
# ============================================================================

@pytest.fixture
def mock_user_store_response():
    """Mock response from user-store service."""
    return {
        "id": fake.uuid4(),
        "name": fake.name(),
        "role": "Backend Developer",
        "seniority": "senior",
        "topics": ["Python", "FastAPI"],
        "tags": ["backend"],
        "subscribed_services": ["user-store"],
        "created_at": fake.iso8601()
    }


@pytest.fixture
def mock_document_store_response():
    """Mock response from doc-store service."""
    return [
        {
            "id": fake.uuid4(),
            "title": "Building Microservices with FastAPI",
            "author_id": fake.uuid4(),
            "created_at": fake.iso8601()
        },
        {
            "id": fake.uuid4(),
            "title": "Python Best Practices",
            "author_id": fake.uuid4(),
            "created_at": fake.iso8601()
        }
    ]


@pytest.fixture
def mock_service_store_response():
    """Mock response from external-service-store."""
    return [
        {
            "service_name": "user-store",
            "user_id": fake.uuid4(),
            "role": "contributor"
        }
    ]


# ============================================================================
# Scoring Fixtures
# ============================================================================

@pytest.fixture
def default_scoring_weights() -> Dict[str, float]:
    """Default scoring weights for testing."""
    return {
        "role_weight": 0.30,
        "topic_weight": 0.40,
        "service_weight": 0.20,
        "document_weight": 0.10
    }


# ============================================================================
# Settings Fixtures
# ============================================================================

@pytest.fixture
def test_settings():
    """Test settings configuration."""
    from infrastructure.config.settings import Settings
    
    return Settings(
        service_name="expert-finder-service",
        service_version="1.0.0",
        service_port=5160,
        user_store_url="http://mock-user-store:5120",
        doc_store_url="http://mock-doc-store:5130",
        service_store_url="http://mock-service-store:5170",
        role_weight=0.30,
        topic_weight=0.40,
        service_weight=0.20,
        document_weight=0.10,
        http_timeout=10.0,
        http_retry_attempts=3,
        sme_min_documents=10,
        sme_min_score=0.7,
        default_results=10,
        max_results=100
    )


# ============================================================================
# FastAPI Fixtures
# ============================================================================

@pytest.fixture
def test_app():
    """FastAPI test application."""
    from fastapi.testclient import TestClient
    from main import app
    
    return TestClient(app)


# ============================================================================
# Async HTTP Client Fixtures
# ============================================================================

@pytest.fixture
async def mock_httpx_client(mocker):
    """Mock httpx.AsyncClient for testing."""
    mock_client = mocker.AsyncMock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_client.get.return_value = mock_response
    return mock_client

