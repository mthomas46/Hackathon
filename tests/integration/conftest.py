"""
Pytest configuration and fixtures for integration tests.
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any


# Service URLs
EXPERT_FINDER_URL = "http://localhost:5160"
USER_STORE_URL = "http://localhost:5150"
DOC_STORE_URL = "http://localhost:5087"
EXTERNAL_SERVICE_STORE_URL = "http://localhost:5140"


@pytest.fixture
async def check_services_running():
    """Check if required services are running."""
    services = {
        "expert-finder": EXPERT_FINDER_URL,
        "user-store": USER_STORE_URL,
        "doc-store": DOC_STORE_URL,
        "external-service-store": EXTERNAL_SERVICE_STORE_URL
    }
    
    running = {}
    
    async with httpx.AsyncClient() as client:
        for name, url in services.items():
            try:
                response = await client.get(f"{url}/health", timeout=2.0)
                running[name] = response.status_code == 200
            except (httpx.ConnectError, httpx.TimeoutException):
                running[name] = False
    
    return running


@pytest.fixture
def sample_expert_query() -> Dict[str, Any]:
    """Sample expert search query."""
    return {
        "query": "Who knows Python backend development?",
        "max_results": 5,
        "min_score": 0.0
    }


@pytest.fixture
def sample_expert_query_with_team() -> Dict[str, Any]:
    """Sample expert search query with team filter."""
    return {
        "query": "backend developers",
        "team_id": "team_test_12345",
        "exclude_team": False,
        "max_results": 5
    }


@pytest.fixture
def sample_users_for_testing():
    """Sample user data for integration testing."""
    return [
        {
            "username": "test.user.001",
            "display_name": "Test User One",
            "email": "test.user.001@example.com",
            "role": "developer",
            "topic_interests": ["Python", "Backend", "APIs"],
            "service_subscriptions": ["user-service", "auth-service"],
            "team_id": "team_test_12345"
        },
        {
            "username": "test.user.002",
            "display_name": "Test User Two",
            "email": "test.user.002@example.com",
            "role": "developer",
            "topic_interests": ["React", "Frontend", "TypeScript"],
            "service_subscriptions": ["web-app"],
            "team_id": "team_test_12345"
        },
        {
            "username": "test.user.003",
            "display_name": "Test User Three",
            "email": "test.user.003@example.com",
            "role": "developer",
            "topic_interests": ["Python", "Backend", "Database"],
            "service_subscriptions": ["database-service"],
            "team_id": "team_test_67890"
        }
    ]


@pytest.fixture
async def create_test_users(sample_users_for_testing):
    """Create test users in user-store for integration testing."""
    created_users = []
    
    async with httpx.AsyncClient() as client:
        for user_data in sample_users_for_testing:
            try:
                response = await client.post(
                    f"{USER_STORE_URL}/users",
                    json=user_data,
                    timeout=5.0
                )
                
                if response.status_code in [200, 201]:
                    created_users.append(response.json())
            except (httpx.ConnectError, httpx.TimeoutException):
                # If user-store not running, skip fixture
                pytest.skip("user-store not running - cannot create test users")
    
    yield created_users
    
    # Cleanup: Delete test users after tests
    async with httpx.AsyncClient() as client:
        for user in created_users:
            if "user_id" in user:
                try:
                    await client.delete(
                        f"{USER_STORE_URL}/users/{user['user_id']}",
                        timeout=5.0
                    )
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass  # Best effort cleanup


@pytest.fixture
def performance_thresholds() -> Dict[str, float]:
    """Performance thresholds for integration tests."""
    return {
        "health_check_max_ms": 100,
        "expert_search_max_ms": 1000,
        "topic_search_max_ms": 500,
        "sme_search_max_ms": 1000
    }

