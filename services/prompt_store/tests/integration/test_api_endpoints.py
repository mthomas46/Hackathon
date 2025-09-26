"""Comprehensive API endpoint tests for prompt_store service.

Tests all HTTP endpoints using FastAPI TestClient for end-to-end validation.
Covers CRUD operations, domain-specific features, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import uuid
import json


@pytest.mark.integration
class TestPromptStoreAPIEndpoints:
    """Comprehensive API endpoint tests for prompt_store."""

    def test_health_endpoint(self, prompt_store_service: TestClient):
        """Test health endpoint returns correct status."""
        response = prompt_store_service.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "version" in data

    def test_prompt_creation(self, prompt_store_service: TestClient):
        """Test prompt creation endpoint."""
        prompt_data = {
            "name": f"api_test_prompt_{uuid.uuid4().hex[:8]}",
            "category": "api_testing",
            "content": "This is a test prompt for API testing.",
            "description": "Test prompt for API endpoint validation",
            "variables": ["var1", "var2"],
            "tags": ["api", "test"],
            "created_by": "api_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        prompt = data["data"]
        assert "id" in prompt
        assert prompt["name"] == prompt_data["name"]
        assert prompt["category"] == prompt_data["category"]
        assert prompt["content"] == prompt_data["content"]
        assert prompt["version"] == 1

        return prompt["id"]  # Return for use in other tests

    def test_prompt_retrieval(self, prompt_store_service: TestClient):
        """Test prompt retrieval endpoint."""
        # First create a prompt
        prompt_id = self.test_prompt_creation(prompt_store_service)

        # Then retrieve it
        response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        prompt = data["data"]
        assert prompt["id"] == prompt_id
        assert "name" in prompt
        assert "content" in prompt
        assert "version" in prompt

    def test_prompt_update(self, prompt_store_service: TestClient):
        """Test prompt update endpoint."""
        # First create a prompt
        prompt_id = self.test_prompt_creation(prompt_store_service)

        # Update the prompt
        update_data = {
            "content": "Updated content for API testing."
        }

        response = prompt_store_service.put(f"/api/v1/prompts/{prompt_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        prompt = data["data"]
        assert prompt["id"] == prompt_id
        assert prompt["content"] == update_data["content"]
        assert prompt["version"] == 2  # Should be incremented

    def test_prompt_listing(self, prompt_store_service: TestClient):
        """Test prompt listing endpoint."""
        # Create a few test prompts
        prompt_ids = []
        for i in range(3):
            prompt_data = {
                "name": f"list_test_prompt_{i}_{uuid.uuid4().hex[:8]}",
                "category": "list_testing",
                "content": f"Content for list test prompt {i}",
                "created_by": "api_test_user"
            }
            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
            assert response.status_code == 201
            prompt_ids.append(response.json()["data"]["id"])

        # List prompts
        response = prompt_store_service.get("/api/v1/prompts")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        prompts = data["data"]
        assert isinstance(prompts, list)
        assert len(prompts) >= 3  # At least our test prompts

        # Verify our test prompts are in the list
        prompt_names = [p["name"] for p in prompts]
        for i in range(3):
            assert any(f"list_test_prompt_{i}" in name for name in prompt_names)

    def test_prompt_search(self, prompt_store_service: TestClient):
        """Test prompt search endpoint."""
        # Create a searchable prompt
        prompt_data = {
            "name": "searchable_prompt",
            "category": "search_testing",
            "content": "This prompt contains searchable content for testing search functionality.",
            "description": "Search test prompt",
            "tags": ["search", "test"],
            "created_by": "api_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201
        prompt_id = response.json()["data"]["id"]

        # Search for the prompt
        response = prompt_store_service.get("/api/v1/prompts/search?q=searchable")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        results = data["data"]
        assert isinstance(results, list)
        assert len(results) > 0

        # Should find our prompt
        found = any(r["id"] == prompt_id for r in results)
        assert found, "Search should find the created prompt"

    def test_prompt_categories(self, prompt_store_service: TestClient):
        """Test prompt categories endpoint."""
        # Create prompts in different categories
        categories = ["cat_test_1", "cat_test_2"]
        for cat in categories:
            prompt_data = {
                "name": f"category_test_{cat}",
                "category": cat,
                "content": f"Content for category {cat}",
                "created_by": "api_test_user"
            }
            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
            assert response.status_code == 201

        # Get categories
        response = prompt_store_service.get("/api/v1/prompts/categories")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        returned_categories = data["data"]
        assert isinstance(returned_categories, list)
        for cat in categories:
            assert cat in returned_categories

    @pytest.mark.asyncio
    async def test_prompt_refinement_initiation(self, prompt_store_service: TestClient):
        """Test prompt refinement initiation endpoint."""
        # Create a prompt to refine
        prompt_data = {
            "name": "refinement_test_prompt",
            "category": "refinement_testing",
            "content": "Write a simple function.",
            "created_by": "api_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201
        prompt_id = response.json()["data"]["id"]

        # Mock the LLM service call since we can't run actual LLM in tests
        with patch('services.shared.clients.ServiceClients.interpret_query', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "data": {
                    "intent": "refine_prompt",
                    "response_text": "Improved prompt: Write a comprehensive function with documentation."
                }
            }

            refinement_data = {
                "refinement_instructions": "Make it more detailed and add documentation",
                "llm_service": "interpreter",
                "user_id": "api_test_user"
            }

            response = prompt_store_service.post(
                f"/api/v1/prompts/{prompt_id}/refine",
                json=refinement_data
            )
            assert response.status_code == 200

            data = response.json()
            assert "success" in data
            assert data["success"] is True
            assert "data" in data

            result = data["data"]
            assert "session_id" in result
            assert result["status"] == "processing"

    def test_refinement_status_check(self, prompt_store_service: TestClient):
        """Test refinement status check endpoint."""
        # Create a mock session ID (normally would come from refinement initiation)
        session_id = f"session_{uuid.uuid4().hex}"

        # Mock the cache to return session data
        with patch('services.prompt_store.infrastructure.cache.prompt_store_cache.get') as mock_cache:
            mock_cache.return_value = {
                "session_id": session_id,
                "status": "completed",
                "llm_service": "interpreter",
                "refinement_instructions": "Make it better"
            }

            response = prompt_store_service.get(f"/api/v1/refinement/sessions/{session_id}")
            assert response.status_code == 200

            data = response.json()
            assert "success" in data
            assert data["success"] is True
            assert "data" in data

            session = data["data"]
            assert session["session_id"] == session_id
            assert session["status"] == "completed"

    def test_prompt_lifecycle_management(self, prompt_store_service: TestClient):
        """Test prompt lifecycle management endpoints."""
        # Create a prompt
        prompt_data = {
            "name": "lifecycle_test_prompt",
            "category": "lifecycle_testing",
            "content": "Test content for lifecycle management",
            "created_by": "api_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201
        prompt_id = response.json()["data"]["id"]

        # Update lifecycle status
        lifecycle_data = {
            "status": "published",
            "reason": "Ready for production use"
        }

        response = prompt_store_service.put(
            f"/api/v1/prompts/{prompt_id}/lifecycle",
            json=lifecycle_data
        )
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True

        # Get prompts by lifecycle status
        response = prompt_store_service.get("/api/v1/prompts/lifecycle/published")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        # Should find our published prompt
        prompts = data["data"]["prompts"]
        assert isinstance(prompts, list)
        prompt_ids = [p["id"] for p in prompts]
        assert prompt_id in prompt_ids

    def test_prompt_relationships(self, prompt_store_service: TestClient):
        """Test prompt relationships endpoints."""
        # Create two prompts
        prompt1_data = {
            "name": "relationship_test_1",
            "category": "relationship_testing",
            "content": "First prompt for relationship testing",
            "created_by": "api_test_user"
        }

        prompt2_data = {
            "name": "relationship_test_2",
            "category": "relationship_testing",
            "content": "Second prompt for relationship testing",
            "created_by": "api_test_user"
        }

        response1 = prompt_store_service.post("/api/v1/prompts", json=prompt1_data)
        response2 = prompt_store_service.post("/api/v1/prompts", json=prompt2_data)

        assert response1.status_code == 201
        assert response2.status_code == 201

        prompt1_id = response1.json()["data"]["id"]
        prompt2_id = response2.json()["data"]["id"]

        # Create relationship
        relationship_data = {
            "target_prompt_id": prompt2_id,
            "relationship_type": "extends",
            "strength": 0.8,
            "metadata": {"reason": "Extension of base functionality"}
        }

        response = prompt_store_service.post(
            f"/api/v1/prompts/{prompt1_id}/relationships",
            json=relationship_data
        )
        assert response.status_code == 201

        data = response.json()
        assert "success" in data
        assert data["success"] is True

        # Get relationships
        response = prompt_store_service.get(f"/api/v1/prompts/{prompt1_id}/relationships")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        relationships = data["data"]
        assert isinstance(relationships, list)
        assert len(relationships) > 0

    def test_a_b_testing_endpoints(self, prompt_store_service: TestClient):
        """Test A/B testing endpoints."""
        # Create two prompts for A/B testing
        prompt_a_data = {
            "name": "ab_test_prompt_a",
            "category": "ab_testing",
            "content": "Version A content",
            "created_by": "api_test_user"
        }

        prompt_b_data = {
            "name": "ab_test_prompt_b",
            "category": "ab_testing",
            "content": "Version B content",
            "created_by": "api_test_user"
        }

        response_a = prompt_store_service.post("/api/v1/prompts", json=prompt_a_data)
        response_b = prompt_store_service.post("/api/v1/prompts", json=prompt_b_data)

        assert response_a.status_code == 201
        assert response_b.status_code == 201

        prompt_a_id = response_a.json()["data"]["id"]
        prompt_b_id = response_b.json()["data"]["id"]

        # Create A/B test
        ab_test_data = {
            "name": "api_ab_test",
            "description": "A/B test for API testing",
            "prompt_a_id": prompt_a_id,
            "prompt_b_id": prompt_b_id,
            "traffic_split": 0.5,
            "duration_days": 7,
            "metric": "response_quality",
            "created_by": "api_test_user"
        }

        response = prompt_store_service.post("/api/v1/ab-tests", json=ab_test_data)
        assert response.status_code == 201

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        test_id = data["data"]["id"]

        # Get A/B test
        response = prompt_store_service.get(f"/api/v1/ab-tests/{test_id}")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True

        test = data["data"]
        assert test["id"] == test_id
        assert test["name"] == "api_ab_test"

    def test_analytics_endpoints(self, prompt_store_service: TestClient):
        """Test analytics endpoints."""
        # Create a prompt and log some usage
        prompt_data = {
            "name": "analytics_test_prompt",
            "category": "analytics_testing",
            "content": "Test prompt for analytics",
            "created_by": "api_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201
        prompt_id = response.json()["data"]["id"]

        # Log usage
        usage_data = {
            "service_name": "test_service",
            "input_tokens": 100,
            "output_tokens": 50,
            "response_time_ms": 1500,
            "success": True
        }

        response = prompt_store_service.post(f"/api/v1/prompts/{prompt_id}/usage", json=usage_data)
        assert response.status_code == 200

        # Get analytics
        response = prompt_store_service.get("/api/v1/analytics/overview")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        analytics = data["data"]
        assert isinstance(analytics, dict)

    def test_bulk_operations(self, prompt_store_service: TestClient):
        """Test bulk operations endpoints."""
        # Create bulk prompt creation request
        bulk_data = {
            "operation_type": "create_prompts",
            "items": [
                {
                    "name": "bulk_test_1",
                    "category": "bulk_testing",
                    "content": "Bulk created prompt 1",
                    "created_by": "api_test_user"
                },
                {
                    "name": "bulk_test_2",
                    "category": "bulk_testing",
                    "content": "Bulk created prompt 2",
                    "created_by": "api_test_user"
                }
            ],
            "created_by": "api_test_user"
        }

        response = prompt_store_service.post("/api/v1/bulk/operations", json=bulk_data)
        assert response.status_code == 202  # Accepted for async processing

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        operation_id = data["data"]["id"]

        # Check bulk operation status
        response = prompt_store_service.get(f"/api/v1/bulk/operations/{operation_id}")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True

    def test_notifications_endpoints(self, prompt_store_service: TestClient):
        """Test notification endpoints."""
        # Register webhook
        webhook_data = {
            "url": "https://example.com/webhook",
            "events": ["prompt.created", "prompt.updated"],
            "secret": "test_secret",
            "is_active": True,
            "created_by": "api_test_user"
        }

        response = prompt_store_service.post("/api/v1/webhooks", json=webhook_data)
        assert response.status_code == 201

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        webhook_id = data["data"]["id"]

        # List webhooks
        response = prompt_store_service.get("/api/v1/webhooks")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        webhooks = data["data"]
        assert isinstance(webhooks, list)

    # Error handling tests
    def test_prompt_not_found(self, prompt_store_service: TestClient):
        """Test handling of non-existent prompt."""
        response = prompt_store_service.get("/api/v1/prompts/nonexistent-id")
        assert response.status_code == 404

        data = response.json()
        assert "success" in data
        assert data["success"] is False
        assert "error_code" in data
        assert data["error_code"] == "NOT_FOUND"

    def test_invalid_prompt_data(self, prompt_store_service: TestClient):
        """Test handling of invalid prompt data."""
        invalid_data = {
            "name": "",  # Invalid: empty name
            "category": "test",
            "content": "",  # Invalid: empty content
        }

        response = prompt_store_service.post("/api/v1/prompts", json=invalid_data)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "success" in data
        assert data["success"] is False

    def test_unauthorized_access(self, prompt_store_service: TestClient):
        """Test unauthorized access handling."""
        # This would test authentication if implemented
        # For now, just ensure endpoints don't crash
        response = prompt_store_service.get("/api/v1/prompts")
        assert response.status_code in [200, 401, 403]  # Should not crash

    def test_malformed_json(self, prompt_store_service: TestClient):
        """Test handling of malformed JSON."""
        response = prompt_store_service.post(
            "/api/v1/prompts",
            data="invalid json {",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # FastAPI validation error

    def test_large_payload(self, prompt_store_service: TestClient):
        """Test handling of large payloads."""
        large_content = "x" * 100000  # 100KB content
        prompt_data = {
            "name": "large_payload_test",
            "category": "stress_test",
            "content": large_content,
            "created_by": "api_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        # Should either succeed or fail gracefully with appropriate error
        assert response.status_code in [201, 413, 422]

        if response.status_code == 201:
            data = response.json()
            assert "success" in data
            assert data["success"] is True

    # Rate limiting tests (would need rate limiting implementation)
    def test_rate_limiting(self, prompt_store_service: TestClient):
        """Test rate limiting behavior."""
        # This would test rate limiting if implemented
        # For now, just ensure multiple rapid requests work
        for i in range(10):
            response = prompt_store_service.get("/health")
            assert response.status_code == 200

    # CORS tests (would need CORS middleware)
    def test_cors_headers(self, prompt_store_service: TestClient):
        """Test CORS headers are present."""
        response = prompt_store_service.options("/health")
        # CORS headers would be tested here if implemented
        assert response.status_code in [200, 404]  # Should not crash
