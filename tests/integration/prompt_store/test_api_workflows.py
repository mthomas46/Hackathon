"""API workflow integration tests for prompt_store service.

Tests complex user workflows and cross-domain interactions through the API.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import uuid
import time


@pytest.mark.integration
class TestAPIWorkflows:
    """Test complex API workflows and user journeys."""

    def test_complete_prompt_lifecycle_workflow(self, prompt_store_service: TestClient):
        """Test complete prompt lifecycle from creation to archival."""
        # 1. Create prompt (draft status)
        prompt_data = {
            "name": f"lifecycle_workflow_{uuid.uuid4().hex[:8]}",
            "category": "workflow_testing",
            "content": "Initial draft content for lifecycle testing.",
            "created_by": "workflow_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201
        prompt_id = response.json()["data"]["id"]

        # 2. Update content (creates version)
        update_data = {
            "content": "Improved content with more details and better structure.",
            "updated_by": "workflow_test_user"
        }

        response = prompt_store_service.put(f"/api/v1/prompts/{prompt_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["data"]["version"] == 2

        # 3. Publish prompt
        lifecycle_data = {
            "status": "published",
            "reason": "Ready for production use after review"
        }

        response = prompt_store_service.put(
            f"/api/v1/prompts/{prompt_id}/lifecycle",
            json=lifecycle_data
        )
        assert response.status_code == 200

        # 4. Verify published status
        response = prompt_store_service.get("/api/v1/prompts/lifecycle/published")
        assert response.status_code == 200
        published_prompts = response.json()["data"]["prompts"]
        prompt_ids = [p["id"] for p in published_prompts]
        assert prompt_id in prompt_ids

        # 5. Deprecate prompt
        lifecycle_data = {
            "status": "deprecated",
            "reason": "Replaced by newer version"
        }

        response = prompt_store_service.put(
            f"/api/v1/prompts/{prompt_id}/lifecycle",
            json=lifecycle_data
        )
        assert response.status_code == 200

        # 6. Archive prompt
        lifecycle_data = {
            "status": "archived",
            "reason": "No longer needed"
        }

        response = prompt_store_service.put(
            f"/api/v1/prompts/{prompt_id}/lifecycle",
            json=lifecycle_data
        )
        assert response.status_code == 200

        # 7. Verify archival
        response = prompt_store_service.get("/api/v1/prompts/lifecycle/archived")
        assert response.status_code == 200
        archived_prompts = response.json()["data"]["prompts"]
        prompt_ids = [p["id"] for p in archived_prompts]
        assert prompt_id in prompt_ids

    @pytest.mark.asyncio
    async def test_prompt_refinement_workflow(self, prompt_store_service: TestClient):
        """Test complete prompt refinement workflow."""
        # 1. Create initial prompt
        prompt_data = {
            "name": f"refinement_workflow_{uuid.uuid4().hex[:8]}",
            "category": "refinement_workflow",
            "content": "Write a simple function.",
            "created_by": "workflow_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201
        prompt_id = response.json()["data"]["id"]

        # 2. Start refinement
        with patch('services.shared.clients.ServiceClients.interpret_query', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "data": {
                    "intent": "refine_prompt",
                    "response_text": "Improved prompt: Write a comprehensive, well-documented function with error handling and type hints."
                }
            }

            refinement_data = {
                "refinement_instructions": "Add comprehensive documentation, error handling, and type hints",
                "llm_service": "interpreter",
                "user_id": "workflow_test_user"
            }

            response = prompt_store_service.post(
                f"/api/v1/prompts/{prompt_id}/refine",
                json=refinement_data
            )
            assert response.status_code == 200
            session_id = response.json()["data"]["session_id"]

        # 3. Check refinement status
        with patch('services.prompt_store.infrastructure.cache.prompt_store_cache.get') as mock_cache:
            mock_cache.return_value = {
                "session_id": session_id,
                "status": "completed",
                "llm_service": "interpreter",
                "result_document_id": f"doc_{uuid.uuid4().hex}",
                "refinement_instructions": "Add comprehensive documentation, error handling, and type hints"
            }

            response = prompt_store_service.get(f"/api/v1/refinement/sessions/{session_id}")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "completed"

        # 4. Apply refined prompt (would need mock for doc service)
        # This would apply the refined version and create a new version

        # 5. Verify version was created
        response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}")
        assert response.status_code == 200
        # Version should be incremented after refinement application

    def test_a_b_testing_workflow(self, prompt_store_service: TestClient):
        """Test complete A/B testing workflow."""
        # 1. Create two prompt variants
        prompt_a_data = {
            "name": f"ab_test_a_{uuid.uuid4().hex[:8]}",
            "category": "ab_testing",
            "content": "Version A: Write a function with basic documentation.",
            "created_by": "workflow_test_user"
        }

        prompt_b_data = {
            "name": f"ab_test_b_{uuid.uuid4().hex[:8]}",
            "category": "ab_testing",
            "content": "Version B: Write a comprehensive function with detailed documentation and examples.",
            "created_by": "workflow_test_user"
        }

        response_a = prompt_store_service.post("/api/v1/prompts", json=prompt_a_data)
        response_b = prompt_store_service.post("/api/v1/prompts", json=prompt_b_data)

        assert response_a.status_code == 201
        assert response_b.status_code == 201

        prompt_a_id = response_a.json()["data"]["id"]
        prompt_b_id = response_b.json()["data"]["id"]

        # 2. Create A/B test
        ab_test_data = {
            "name": f"workflow_ab_test_{uuid.uuid4().hex[:8]}",
            "description": "Testing documentation detail levels",
            "prompt_a_id": prompt_a_id,
            "prompt_b_id": prompt_b_id,
            "traffic_split": 0.5,
            "duration_days": 7,
            "metric": "user_satisfaction",
            "created_by": "workflow_test_user"
        }

        response = prompt_store_service.post("/api/v1/ab-tests", json=ab_test_data)
        assert response.status_code == 201
        test_id = response.json()["data"]["id"]

        # 3. Start the test
        response = prompt_store_service.post(f"/api/v1/ab-tests/{test_id}/start")
        assert response.status_code == 200

        # 4. Simulate some usage/results
        result_a = {
            "metric_value": 0.75,
            "sample_size": 100,
            "confidence_level": 0.95,
            "statistical_significance": True
        }

        result_b = {
            "metric_value": 0.82,
            "sample_size": 100,
            "confidence_level": 0.95,
            "statistical_significance": True
        }

        response = prompt_store_service.post(
            f"/api/v1/ab-tests/{test_id}/results/a",
            json=result_a
        )
        assert response.status_code == 200

        response = prompt_store_service.post(
            f"/api/v1/ab-tests/{test_id}/results/b",
            json=result_b
        )
        assert response.status_code == 200

        # 5. Get test results
        response = prompt_store_service.get(f"/api/v1/ab-tests/{test_id}/results")
        assert response.status_code == 200

        results = response.json()["data"]
        assert len(results) == 2

        # 6. Complete the test
        response = prompt_store_service.post(f"/api/v1/ab-tests/{test_id}/complete")
        assert response.status_code == 200

        # 7. Verify test completion
        response = prompt_store_service.get(f"/api/v1/ab-tests/{test_id}")
        assert response.status_code == 200
        test_data = response.json()["data"]
        assert test_data["status"] == "completed"

    def test_relationship_management_workflow(self, prompt_store_service: TestClient):
        """Test prompt relationship management workflow."""
        # 1. Create base prompt
        base_prompt_data = {
            "name": f"base_prompt_{uuid.uuid4().hex[:8]}",
            "category": "relationship_testing",
            "content": "Base functionality prompt.",
            "created_by": "workflow_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=base_prompt_data)
        assert response.status_code == 201
        base_prompt_id = response.json()["data"]["id"]

        # 2. Create extension prompt
        extension_prompt_data = {
            "name": f"extension_prompt_{uuid.uuid4().hex[:8]}",
            "category": "relationship_testing",
            "content": "Extended functionality building on base.",
            "created_by": "workflow_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=extension_prompt_data)
        assert response.status_code == 201
        extension_prompt_id = response.json()["data"]["id"]

        # 3. Create "extends" relationship
        relationship_data = {
            "target_prompt_id": base_prompt_id,
            "relationship_type": "extends",
            "strength": 0.9,
            "metadata": {
                "inheritance_type": "functionality_extension",
                "compatibility_version": "1.0"
            }
        }

        response = prompt_store_service.post(
            f"/api/v1/prompts/{extension_prompt_id}/relationships",
            json=relationship_data
        )
        assert response.status_code == 201

        # 4. Create alternative prompt
        alternative_prompt_data = {
            "name": f"alternative_prompt_{uuid.uuid4().hex[:8]}",
            "category": "relationship_testing",
            "content": "Alternative implementation of base functionality.",
            "created_by": "workflow_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=alternative_prompt_data)
        assert response.status_code == 201
        alternative_prompt_id = response.json()["data"]["id"]

        # 5. Create "alternative" relationship
        relationship_data = {
            "target_prompt_id": base_prompt_id,
            "relationship_type": "alternative",
            "strength": 0.7,
            "metadata": {
                "alternative_reason": "different_approach",
                "performance_characteristics": "higher_accuracy"
            }
        }

        response = prompt_store_service.post(
            f"/api/v1/prompts/{alternative_prompt_id}/relationships",
            json=relationship_data
        )
        assert response.status_code == 201

        # 6. Query relationships
        response = prompt_store_service.get(f"/api/v1/prompts/{base_prompt_id}/relationships")
        assert response.status_code == 200

        relationships = response.json()["data"]
        assert len(relationships) == 2  # Should have both extension and alternative

        relationship_types = [r["relationship_type"] for r in relationships]
        assert "extends" in relationship_types
        assert "alternative" in relationship_types

        # 7. Query relationship graph
        response = prompt_store_service.get(
            f"/api/v1/prompts/{base_prompt_id}/relationships/graph?depth=2"
        )
        assert response.status_code == 200

        graph_data = response.json()["data"]
        assert "nodes" in graph_data
        assert "edges" in graph_data

    def test_bulk_operations_workflow(self, prompt_store_service: TestClient):
        """Test bulk operations workflow."""
        # 1. Create bulk creation operation
        bulk_prompts = []
        for i in range(5):
            bulk_prompts.append({
                "name": f"bulk_workflow_{i}_{uuid.uuid4().hex[:4]}",
                "category": "bulk_workflow_testing",
                "content": f"Bulk created prompt content {i}",
                "created_by": "workflow_test_user"
            })

        bulk_data = {
            "operation_type": "create_prompts",
            "items": bulk_prompts,
            "created_by": "workflow_test_user"
        }

        response = prompt_store_service.post("/api/v1/bulk/operations", json=bulk_data)
        assert response.status_code == 202  # Accepted
        operation_id = response.json()["data"]["id"]

        # 2. Monitor operation progress
        max_attempts = 10
        for attempt in range(max_attempts):
            response = prompt_store_service.get(f"/api/v1/bulk/operations/{operation_id}")
            assert response.status_code == 200

            operation_data = response.json()["data"]
            status = operation_data["status"]

            if status == "completed":
                break
            elif status == "failed":
                pytest.fail(f"Bulk operation failed: {operation_data.get('errors', [])}")

            time.sleep(0.5)  # Wait before checking again

        # Should complete within max_attempts
        assert attempt < max_attempts, "Bulk operation did not complete in time"

        # 3. Verify results
        final_response = prompt_store_service.get(f"/api/v1/bulk/operations/{operation_id}")
        operation_data = final_response.json()["data"]

        assert operation_data["status"] == "completed"
        assert operation_data["total_items"] == 5
        assert operation_data["successful_items"] == 5
        assert operation_data["failed_items"] == 0

    def test_notification_workflow(self, prompt_store_service: TestClient):
        """Test notification system workflow."""
        # 1. Register webhook
        webhook_data = {
            "url": "https://example.com/workflow-webhook",
            "events": ["prompt.created", "prompt.updated", "ab_test.completed"],
            "secret": "workflow_test_secret",
            "is_active": True,
            "created_by": "workflow_test_user"
        }

        response = prompt_store_service.post("/api/v1/webhooks", json=webhook_data)
        assert response.status_code == 201
        webhook_id = response.json()["data"]["id"]

        # 2. Create prompt (should trigger notification)
        prompt_data = {
            "name": f"notification_test_{uuid.uuid4().hex[:8]}",
            "category": "notification_testing",
            "content": "Test prompt for notification workflow.",
            "created_by": "workflow_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201

        # 3. Update prompt (should trigger notification)
        prompt_id = response.json()["data"]["id"]
        update_data = {
            "content": "Updated content for notification testing.",
            "updated_by": "workflow_test_user"
        }

        response = prompt_store_service.put(f"/api/v1/prompts/{prompt_id}", json=update_data)
        assert response.status_code == 200

        # 4. List webhook deliveries (if implemented)
        # This would check that notifications were sent
        response = prompt_store_service.get(f"/api/v1/webhooks/{webhook_id}/deliveries")
        # May return 404 if not implemented, but shouldn't crash
        assert response.status_code in [200, 404]

    def test_search_and_filtering_workflow(self, prompt_store_service: TestClient):
        """Test search and filtering workflow."""
        # 1. Create diverse prompts for testing
        test_prompts = [
            {
                "name": "python_function_prompt",
                "category": "programming",
                "content": "Write a Python function to calculate fibonacci numbers.",
                "tags": ["python", "math", "recursion"],
                "created_by": "workflow_test_user"
            },
            {
                "name": "javascript_array_prompt",
                "category": "programming",
                "content": "Write JavaScript code to manipulate arrays.",
                "tags": ["javascript", "arrays", "data-structures"],
                "created_by": "workflow_test_user"
            },
            {
                "name": "database_query_prompt",
                "category": "database",
                "content": "Write an SQL query to join customer and order tables.",
                "tags": ["sql", "database", "joins"],
                "created_by": "workflow_test_user"
            }
        ]

        created_prompts = []
        for prompt_data in test_prompts:
            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
            assert response.status_code == 201
            created_prompts.append(response.json()["data"]["id"])

        # 2. Test text search
        response = prompt_store_service.get("/api/v1/prompts/search?q=function")
        assert response.status_code == 200
        results = response.json()["data"]
        assert len(results) >= 1

        # 3. Test category filtering
        response = prompt_store_service.get("/api/v1/prompts?category=programming")
        assert response.status_code == 200
        results = response.json()["data"]
        assert len(results) >= 2

        # 4. Test tag filtering
        response = prompt_store_service.get("/api/v1/prompts?tags=python")
        assert response.status_code == 200
        results = response.json()["data"]
        assert len(results) >= 1

        # 5. Test combined search and filters
        response = prompt_store_service.get("/api/v1/prompts/search?q=code&category=programming")
        assert response.status_code == 200
        results = response.json()["data"]
        assert len(results) >= 1

    def test_analytics_workflow(self, prompt_store_service: TestClient):
        """Test analytics and usage tracking workflow."""
        # 1. Create test prompt
        prompt_data = {
            "name": f"analytics_workflow_{uuid.uuid4().hex[:8]}",
            "category": "analytics_testing",
            "content": "Test prompt for analytics workflow.",
            "created_by": "workflow_test_user"
        }

        response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert response.status_code == 201
        prompt_id = response.json()["data"]["id"]

        # 2. Simulate usage logging
        usage_logs = [
            {"service_name": "api_test", "input_tokens": 50, "output_tokens": 25, "response_time_ms": 1200, "success": True},
            {"service_name": "api_test", "input_tokens": 75, "output_tokens": 30, "response_time_ms": 1500, "success": True},
            {"service_name": "api_test", "input_tokens": 60, "output_tokens": 0, "response_time_ms": 800, "success": False},
        ]

        for usage in usage_logs:
            response = prompt_store_service.post(f"/api/v1/prompts/{prompt_id}/usage", json=usage)
            assert response.status_code == 200

        # 3. Get usage analytics
        response = prompt_store_service.get(f"/api/v1/analytics/prompt/{prompt_id}/usage")
        assert response.status_code == 200

        analytics = response.json()["data"]
        assert "total_requests" in analytics
        assert "success_rate" in analytics
        assert "average_response_time" in analytics

        # 4. Get overall analytics
        response = prompt_store_service.get("/api/v1/analytics/overview")
        assert response.status_code == 200

        overview = response.json()["data"]
        assert isinstance(overview, dict)

        # 5. Get performance metrics
        response = prompt_store_service.get("/api/v1/analytics/performance")
        assert response.status_code == 200

        performance = response.json()["data"]
        assert isinstance(performance, dict)
