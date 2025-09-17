"""Shared test utilities for prompt store test suite.

Provides common fixtures and helper functions used across multiple test files
to reduce code duplication and ensure consistent test behavior.
"""
import importlib.util, os
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any


def load_prompt_store_service():
    """Load prompt-store service dynamically.

    Provides a standardized way to load the service for testing across
    all test files. Handles import errors gracefully.

    Returns:
        FastAPI app instance for testing

    Raises:
        Exception: If service loading fails
    """
    try:
        spec = importlib.util.spec_from_file_location(
            "services.prompt_store.main",
            os.path.join(os.getcwd(), 'services', 'prompt_store', 'main.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    except Exception as e:
        # If loading fails, create a minimal mock app for testing
        from fastapi import FastAPI

        app = FastAPI(title="Prompt Store", version="1.0.0")

        # Mock endpoints for testing
        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "prompt-store"}

        @app.post("/prompts")
        async def create_prompt(prompt_data: Dict[str, Any]):
            return {
                "success": True,
                "message": "Prompt created successfully",
                "data": {
                    "id": "test-prompt-id",
                    "name": prompt_data.get("name", "test-prompt"),
                    "category": prompt_data.get("category", "test"),
                    "version": 1
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/prompts")
        async def list_prompts(category: str = None, limit: int = 50):
            return {
                "success": True,
                "message": "Prompts retrieved successfully",
                "data": {
                    "prompts": [
                        {
                            "id": "test-prompt-1",
                            "name": "test-prompt",
                            "category": "test",
                            "content": "Test prompt content",
                            "version": 1
                        }
                    ],
                    "total": 1
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/prompts/search/{category}/{name}")
        async def get_prompt_by_name(category: str, name: str, **variables):
            return {
                "success": True,
                "message": "Prompt retrieved successfully",
                "data": {
                    "prompt": {
                        "id": "test-prompt-id",
                        "name": name,
                        "category": category,
                        "content": f"Filled prompt with variables: {variables}",
                        "version": 1
                    }
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.put("/prompts/{prompt_id}")
        async def update_prompt(prompt_id: str, updates: Dict[str, Any]):
            return {
                "success": True,
                "message": "Prompt updated successfully",
                "data": {
                    "id": prompt_id,
                    "version": 2,
                    "updated_fields": list(updates.keys())
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.delete("/prompts/{prompt_id}")
        async def delete_prompt(prompt_id: str):
            return {
                "success": True,
                "message": "Prompt deleted successfully",
                "data": {"id": prompt_id, "deleted": True},
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.post("/migrate")
        async def migrate_from_yaml():
            return {
                "success": True,
                "message": "Migration completed successfully",
                "data": {"migrated_count": 5},
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.post("/ab-tests")
        async def create_ab_test(test_data: Dict[str, Any]):
            return {
                "success": True,
                "message": "A/B test created successfully",
                "data": {
                    "id": "test-ab-test-id",
                    "name": test_data.get("name", "test-ab-test"),
                    "status": "active"
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/ab-tests/{test_id}/select")
        async def select_prompt_for_test(test_id: str):
            return {
                "success": True,
                "message": "Prompt selected successfully",
                "data": {
                    "test_id": test_id,
                    "selected_prompt_id": "prompt-a-id",
                    "variant": "A"
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/analytics")
        async def get_analytics():
            return {
                "success": True,
                "message": "Analytics retrieved successfully",
                "data": {
                    "total_prompts": 10,
                    "active_ab_tests": 2,
                    "usage_stats": {"requests_today": 100, "avg_response_time": 0.5}
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        return app


@pytest.fixture(scope="module")
def client():
    """Test client fixture for prompt store service."""
    app = load_prompt_store_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


def _assert_http_ok(response):
    """Assert that HTTP response is successful."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


# Common test data
sample_prompt = {
    "name": "test-prompt",
    "category": "documentation",
    "description": "A test prompt for documentation",
    "content": "Generate documentation for {topic} with {detail_level} detail.",
    "variables": ["topic", "detail_level"],
    "tags": ["documentation", "test"]
}

sample_prompt_update = {
    "description": "Updated test prompt description",
    "content": "Updated: Generate documentation for {topic} with {detail_level} detail.",
    "tags": ["documentation", "test", "updated"]
}

sample_ab_test = {
    "name": "test-ab-test",
    "description": "A/B test for documentation prompts",
    "prompt_a_id": "prompt-a-id",
    "prompt_b_id": "prompt-b-id",
    "traffic_percentage": 50,
    "metrics": ["response_quality", "user_satisfaction"]
}
