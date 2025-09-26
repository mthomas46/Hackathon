"""API integration tests for Prompt Store service.

Tests full HTTP request/response cycles across all domains.
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.prompt_store
class TestPromptAPIIntegration:
    """Test prompt management API endpoints."""

    def test_prompt_crud_workflow(self, prompt_store_service):
        """Test complete prompt CRUD workflow via API."""
        # Create prompt
        prompt_data = {
            "name": "api_integration_prompt",
            "category": "api_test",
            "content": "Content for API integration testing",
            "variables": ["var1", "var2"],
            "is_template": True
        }

        create_response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert create_data["success"] is True
        prompt_id = create_data["data"]["id"]

        # Get prompt
        get_response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["success"] is True
        assert get_data["data"]["name"] == "api_integration_prompt"

        # Update prompt
        update_data = {"content": "Updated content for API testing"}
        update_response = prompt_store_service.put(f"/api/v1/prompts/{prompt_id}", json=update_data)
        assert update_response.status_code == 200

        # Verify update
        verify_response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}")
        verify_data = verify_response.json()
        assert verify_data["data"]["content"] == "Updated content for API testing"

    def test_prompt_search_and_filtering(self, prompt_store_service):
        """Test prompt search and filtering capabilities."""
        # Create multiple prompts for testing
        prompts_data = [
            {"name": "search_test_1", "category": "search", "content": "Python development"},
            {"name": "search_test_2", "category": "search", "content": "JavaScript programming"},
            {"name": "search_test_3", "category": "filter", "content": "Data analysis"}
        ]

        prompt_ids = []
        for prompt_data in prompts_data:
            response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
            assert response.status_code == 200
            prompt_ids.append(response.json()["data"]["id"])

        # Test category filtering
        category_response = prompt_store_service.get("/api/v1/prompts/category/search")
        assert category_response.status_code == 200
        category_data = category_response.json()
        assert category_data["success"] is True
        assert len(category_data["data"]["prompts"]) >= 2

        # Test search
        search_response = prompt_store_service.post("/api/v1/prompts/search", json={
            "query": "Python",
            "category": "search"
        })
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["success"] is True


@pytest.mark.integration
@pytest.mark.prompt_store
class TestLifecycleAPIIntegration:
    """Test lifecycle management API endpoints."""

    def test_lifecycle_workflow(self, prompt_store_service):
        """Test complete lifecycle workflow via API."""
        # Create prompt
        prompt_data = {
            "name": "lifecycle_api_test",
            "category": "lifecycle",
            "content": "Content for lifecycle API testing"
        }

        create_response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        assert create_response.status_code == 200
        prompt_id = create_response.json()["data"]["id"]

        # Check initial status
        get_response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}")
        initial_status = get_response.json()["data"]["lifecycle_status"]
        assert initial_status == "draft"

        # Update to published
        lifecycle_data = {"status": "published", "reason": "API testing"}
        update_response = prompt_store_service.put(f"/api/v1/prompts/{prompt_id}/lifecycle", json=lifecycle_data)
        assert update_response.status_code == 200

        # Verify status change
        verify_response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}")
        assert verify_response.json()["data"]["lifecycle_status"] == "published"

        # Get lifecycle history
        history_response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}/lifecycle/history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert history_data["success"] is True
        assert len(history_data["data"]["lifecycle_history"]) >= 1

        # Get lifecycle counts
        counts_response = prompt_store_service.get("/api/v1/lifecycle/counts")
        assert counts_response.status_code == 200
        counts_data = counts_response.json()
        assert counts_data["success"] is True
        assert "published" in counts_data["data"]["status_counts"]


@pytest.mark.integration
@pytest.mark.prompt_store
class TestRelationshipsAPIIntegration:
    """Test relationships management API endpoints."""

    def test_relationship_workflow(self, prompt_store_service):
        """Test complete relationship workflow via API."""
        # Create two prompts
        prompt1_data = {"name": "rel_api_test_1", "category": "relationships", "content": "Base prompt"}
        prompt2_data = {"name": "rel_api_test_2", "category": "relationships", "content": "Extension prompt"}

        prompt1_response = prompt_store_service.post("/api/v1/prompts", json=prompt1_data)
        prompt2_response = prompt_store_service.post("/api/v1/prompts", json=prompt2_data)

        prompt1_id = prompt1_response.json()["data"]["id"]
        prompt2_id = prompt2_response.json()["data"]["id"]

        # Create relationship
        relationship_data = {
            "target_prompt_id": prompt2_id,
            "relationship_type": "extends",
            "strength": 0.8,
            "metadata": {"api_test": True}
        }

        create_response = prompt_store_service.post(f"/api/v1/prompts/{prompt1_id}/relationships", json=relationship_data)
        assert create_response.status_code == 200

        # Get relationships
        get_response = prompt_store_service.get(f"/api/v1/prompts/{prompt1_id}/relationships")
        assert get_response.status_code == 200
        relationships_data = get_response.json()
        assert relationships_data["success"] is True
        assert len(relationships_data["data"]["outgoing_relationships"]) >= 1

        # Get relationship graph
        graph_response = prompt_store_service.get(f"/api/v1/prompts/{prompt1_id}/relationships/graph")
        assert graph_response.status_code == 200
        graph_data = graph_response.json()
        assert graph_data["success"] is True
        assert graph_data["data"]["total_nodes"] >= 2

        # Get relationship stats
        stats_response = prompt_store_service.get("/api/v1/relationships/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["success"] is True
        assert "extends" in stats_data["data"]["relationship_counts"]


@pytest.mark.integration
@pytest.mark.prompt_store
class TestNotificationsAPIIntegration:
    """Test notifications and webhooks API endpoints."""

    def test_webhook_workflow(self, prompt_store_service):
        """Test complete webhook workflow via API."""
        # Register webhook
        webhook_data = {
            "name": "api_test_webhook",
            "url": "https://httpbin.org/post",
            "events": ["prompt.created", "prompt.updated"],
            "secret": "api_test_secret",
            "is_active": True
        }

        register_response = prompt_store_service.post("/api/v1/webhooks", json=webhook_data)
        assert register_response.status_code == 200
        webhook_data = register_response.json()
        assert webhook_data["success"] is True
        webhook_id = webhook_data["data"]["webhook_id"]

        # List webhooks
        list_response = prompt_store_service.get("/api/v1/webhooks")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["success"] is True
        assert list_data["data"]["count"] >= 1

        # Get specific webhook
        get_response = prompt_store_service.get(f"/api/v1/webhooks/{webhook_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["success"] is True
        assert get_data["data"]["name"] == "api_test_webhook"

        # Get notification stats
        stats_response = prompt_store_service.get("/api/v1/notifications/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["success"] is True

    def test_event_triggering(self, prompt_store_service):
        """Test manual event triggering via API."""
        # Register webhook first
        webhook_data = {
            "name": "event_trigger_webhook",
            "url": "https://httpbin.org/post",
            "events": ["test.event"],
            "is_active": True
        }

        register_response = prompt_store_service.post("/api/v1/webhooks", json=webhook_data)
        webhook_id = register_response.json()["data"]["webhook_id"]

        # Trigger event
        event_data = {
            "event_type": "test.event",
            "event_data": {"test_key": "test_value"}
        }

        trigger_response = prompt_store_service.post("/api/v1/notifications/trigger", json=event_data)
        assert trigger_response.status_code == 200
        trigger_data = trigger_response.json()
        assert trigger_data["success"] is True

        # Check notification stats increased
        stats_response = prompt_store_service.get("/api/v1/notifications/stats")
        stats_data = stats_response.json()
        assert stats_data["data"]["total_notifications"] >= 1


@pytest.mark.integration
@pytest.mark.prompt_store
class TestABTestingAPIIntegration:
    """Test A/B testing API endpoints."""

    def test_ab_test_workflow(self, prompt_store_service):
        """Test complete A/B testing workflow via API."""
        # Create two prompts
        prompt_a_data = {"name": "ab_test_a", "category": "ab_test", "content": "Version A"}
        prompt_b_data = {"name": "ab_test_b", "category": "ab_test", "content": "Version B"}

        prompt_a_response = prompt_store_service.post("/api/v1/prompts", json=prompt_a_data)
        prompt_b_response = prompt_store_service.post("/api/v1/prompts", json=prompt_b_data)

        prompt_a_id = prompt_a_response.json()["data"]["id"]
        prompt_b_id = prompt_b_response.json()["data"]["id"]

        # Create A/B test
        ab_test_data = {
            "name": "api_ab_test",
            "description": "A/B test via API",
            "prompt_a_id": prompt_a_id,
            "prompt_b_id": prompt_b_id,
            "traffic_percentage": 50
        }

        create_response = prompt_store_service.post("/api/v1/ab-tests", json=ab_test_data)
        assert create_response.status_code == 200
        ab_test_data = create_response.json()
        assert ab_test_data["success"] is True
        ab_test_id = ab_test_data["data"]["id"]

        # Get A/B test
        get_response = prompt_store_service.get(f"/api/v1/ab-tests/{ab_test_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["success"] is True
        assert get_data["data"]["name"] == "api_ab_test"

        # Select variant
        select_response = prompt_store_service.get(f"/api/v1/ab-tests/{ab_test_id}/select?user_id=test_user")
        assert select_response.status_code == 200
        select_data = select_response.json()
        assert select_data["success"] is True
        assert "selected_prompt_id" in select_data["data"]

        # Get test results
        results_response = prompt_store_service.get(f"/api/v1/ab-tests/{ab_test_id}/results")
        assert results_response.status_code == 200
        results_data = results_response.json()
        assert results_data["success"] is True


@pytest.mark.integration
@pytest.mark.prompt_store
class TestBulkOperationsAPIIntegration:
    """Test bulk operations API endpoints."""

    def test_bulk_operation_workflow(self, prompt_store_service):
        """Test bulk operation workflow via API."""
        # Create bulk operation
        bulk_data = {
            "operation_type": "create_prompts",
            "total_items": 10,
            "metadata": {"source": "api_test"}
        }

        create_response = prompt_store_service.post("/api/v1/bulk/prompts", json=bulk_data)
        assert create_response.status_code == 200
        bulk_data = create_response.json()
        assert bulk_data["success"] is True
        bulk_operation_id = bulk_data["data"]["id"]

        # Get operation status
        status_response = prompt_store_service.get(f"/api/v1/bulk/operations/{bulk_operation_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["success"] is True
        assert status_data["data"]["status"] == "pending"

        # List bulk operations
        list_response = prompt_store_service.get("/api/v1/bulk/operations")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["success"] is True
        assert len(list_data["data"]["operations"]) >= 1


@pytest.mark.integration
@pytest.mark.prompt_store
class TestAnalyticsAPIIntegration:
    """Test analytics API endpoints."""

    def test_analytics_workflow(self, prompt_store_service):
        """Test analytics functionality via API."""
        # Create some test data first
        for i in range(3):
            prompt_data = {
                "name": f"analytics_api_test_{i}",
                "category": "analytics_test",
                "content": f"Content for analytics test {i}"
            }
            prompt_store_service.post("/api/v1/prompts", json=prompt_data)

        # Get summary analytics
        summary_response = prompt_store_service.get("/api/v1/analytics/summary")
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        assert summary_data["success"] is True
        assert "total_prompts" in summary_data["data"]

        # Get usage analytics
        usage_response = prompt_store_service.get("/api/v1/analytics/usage")
        assert usage_response.status_code == 200
        usage_data = usage_response.json()
        assert usage_data["success"] is True


@pytest.mark.integration
@pytest.mark.prompt_store
class TestRefinementAPIIntegration:
    """Test refinement API endpoints."""

    def test_refinement_workflow(self, prompt_store_service):
        """Test refinement workflow via API."""
        # Create a prompt to refine
        prompt_data = {
            "name": "refinement_api_test",
            "category": "refinement",
            "content": "Original prompt content for refinement"
        }

        prompt_response = prompt_store_service.post("/api/v1/prompts", json=prompt_data)
        prompt_id = prompt_response.json()["data"]["id"]

        # Start refinement
        refinement_data = {
            "refinement_instructions": "Make this prompt more specific",
            "llm_service": "interpreter",
            "user_id": "api_test_user"
        }

        refine_response = prompt_store_service.post(f"/api/v1/prompts/{prompt_id}/refine", json=refinement_data)
        assert refine_response.status_code == 200
        refine_data = refine_response.json()
        assert refine_data["success"] is True
        session_id = refine_data["data"]["session_id"]

        # Get refinement status
        status_response = prompt_store_service.get(f"/api/v1/refinement/sessions/{session_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["success"] is True

        # Get refinement history
        history_response = prompt_store_service.get(f"/api/v1/prompts/{prompt_id}/refinement/history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert history_data["success"] is True
