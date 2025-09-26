"""Integration tests for cross-domain workflows in Prompt Store.

Tests complex interactions between multiple domains to ensure end-to-end functionality.
"""

import pytest
import asyncio
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.prompt_store
class TestPromptLifecycleWorkflow:
    """Test complete prompt lifecycle workflow across domains."""

    def test_complete_prompt_lifecycle_with_notifications(self, prompt_store_db):
        """Test full prompt lifecycle with notifications and analytics."""
        # Create prompt
        from services.prompt_store.domain.prompts.service import PromptService
        from services.prompt_store.domain.lifecycle.service import LifecycleService
        from services.prompt_store.domain.notifications.service import NotificationsService
        from services.prompt_store.domain.analytics.service import AnalyticsService

        prompt_service = PromptService()
        lifecycle_service = LifecycleService()
        notifications_service = NotificationsService()
        analytics_service = AnalyticsService()

        # Step 1: Create prompt (should trigger prompt.created notification)
        prompt = prompt_service.create_entity({
            "name": "lifecycle_test_prompt",
            "category": "integration_test",
            "content": "Test prompt for lifecycle workflow",
            "created_by": "integration_test"
        })

        assert prompt.lifecycle_status == "draft"

        # Step 2: Register webhook for notifications
        webhook_result = notifications_service.register_webhook({
            "name": "integration_test_webhook",
            "url": "https://httpbin.org/post",
            "events": ["prompt.lifecycle_changed", "prompt.updated"],
            "secret": "integration_secret",
            "is_active": True,
            "created_by": "integration_test"
        })

        # Step 3: Update lifecycle to published (should trigger notification)
        lifecycle_result = lifecycle_service.update_lifecycle_status(
            prompt.id, "published", "Publishing for integration test", "integration_test"
        )

        assert lifecycle_result["previous_status"] == "draft"
        assert lifecycle_result["new_status"] == "published"

        # Verify prompt status updated
        updated_prompt = prompt_service.get_entity(prompt.id)
        assert updated_prompt.lifecycle_status == "published"

        # Step 4: Record some analytics (usage events)
        from services.prompt_store.domain.analytics.repository import AnalyticsRepository
        analytics_repo = AnalyticsRepository()

        analytics_repo.record_usage_event({
            "prompt_id": prompt.id,
            "user_id": "test_user_1",
            "session_id": "session_123",
            "event_type": "usage",
            "metric_value": 0.85,
            "metadata": {"model": "gpt-4", "tokens": 150}
        })

        # Step 5: Check analytics
        analytics = analytics_service.get_prompt_analytics(prompt.id)
        assert analytics["prompt_id"] == prompt.id
        assert "performance_metrics" in analytics
        assert "usage_trends" in analytics

        # Step 6: Check notification stats
        notification_stats = notifications_service.get_notification_stats()
        assert "total_notifications" in notification_stats
        assert notification_stats["total_notifications"] >= 1  # At least the lifecycle change

    def test_prompt_relationships_with_lifecycle(self, prompt_store_db):
        """Test prompt relationships combined with lifecycle management."""
        from services.prompt_store.domain.prompts.service import PromptService
        from services.prompt_store.domain.relationships.service import RelationshipsService
        from services.prompt_store.domain.lifecycle.service import LifecycleService

        prompt_service = PromptService()
        relationships_service = RelationshipsService()
        lifecycle_service = LifecycleService()

        # Create two prompts
        prompt_a = prompt_service.create_entity({
            "name": "relationship_base",
            "category": "integration_test",
            "content": "Base prompt for relationship testing",
            "created_by": "integration_test"
        })

        prompt_b = prompt_service.create_entity({
            "name": "relationship_extension",
            "category": "integration_test",
            "content": "Extension of base prompt",
            "created_by": "integration_test"
        })

        # Create relationship between prompts
        relationship_result = relationships_service.create_relationship(
            prompt_a.id,
            {
                "target_prompt_id": prompt_b.id,
                "relationship_type": "extends",
                "strength": 0.9,
                "metadata": {"inheritance_level": 1}
            },
            "integration_test"
        )

        assert relationship_result["relationship_type"] == "extends"
        assert relationship_result["source_prompt_id"] == prompt_a.id
        assert relationship_result["target_prompt_id"] == prompt_b.id

        # Publish the base prompt
        lifecycle_service.update_lifecycle_status(
            prompt_a.id, "published", "Publishing base prompt", "integration_test"
        )

        # Check that relationships are maintained
        relationships = relationships_service.get_relationships_for_prompt(prompt_a.id)
        assert len(relationships["outgoing_relationships"]) == 1
        assert relationships["outgoing_relationships"][0]["relationship_type"] == "extends"

        # Archive the base prompt
        lifecycle_service.update_lifecycle_status(
            prompt_a.id, "archived", "Archiving for cleanup", "integration_test"
        )

        # Verify archived status
        archived_prompt = prompt_service.get_entity(prompt_a.id)
        assert archived_prompt.lifecycle_status == "archived"


@pytest.mark.integration
@pytest.mark.prompt_store
class TestABTestingWorkflow:
    """Test A/B testing workflows with analytics and notifications."""

    def test_ab_test_creation_and_execution(self, prompt_store_db):
        """Test complete A/B testing workflow."""
        from services.prompt_store.domain.prompts.service import PromptService
        from services.prompt_store.domain.ab_testing.service import ABTestService
        from services.prompt_store.domain.analytics.service import AnalyticsService
        from services.prompt_store.domain.notifications.service import NotificationsService

        prompt_service = PromptService()
        ab_test_service = ABTestService()
        analytics_service = AnalyticsService()
        notifications_service = NotificationsService()

        # Create test prompts
        prompt_a = prompt_service.create_entity({
            "name": "ab_test_version_a",
            "category": "ab_test",
            "content": "Version A of test prompt",
            "created_by": "integration_test"
        })

        prompt_b = prompt_service.create_entity({
            "name": "ab_test_version_b",
            "category": "ab_test",
            "content": "Version B of test prompt",
            "created_by": "integration_test"
        })

        # Create A/B test
        ab_test = ab_test_service.create_ab_test({
            "name": "integration_ab_test",
            "description": "Integration test for A/B testing workflow",
            "prompt_a_id": prompt_a.id,
            "prompt_b_id": prompt_b.id,
            "traffic_percentage": 50,
            "created_by": "integration_test"
        })

        assert ab_test["name"] == "integration_ab_test"
        assert ab_test["status"] == "active"

        # Simulate user interactions
        test_users = ["user_1", "user_2", "user_3", "user_4", "user_5"]

        for user_id in test_users:
            # Select variant for user
            selected_variant = ab_test_service.select_prompt_variant(ab_test["id"], user_id)
            assert selected_variant in [prompt_a.id, prompt_b.id]

            # Record test result
            ab_test_service.record_test_result(
                ab_test["id"], selected_variant, 0.8, 100, f"session_{user_id}"
            )

        # Get test results
        results = ab_test_service.get_test_results(ab_test["id"])
        assert len(results) >= len(test_users)

        # Check analytics integration
        summary_stats = analytics_service.get_summary_stats()
        assert "total_prompts" in summary_stats
        assert summary_stats["total_prompts"] >= 2  # At least the two test prompts

    def test_bulk_operations_with_notifications(self, prompt_store_db):
        """Test bulk operations combined with notification system."""
        from services.prompt_store.domain.prompts.service import PromptService
        from services.prompt_store.domain.bulk.service import BulkOperationService
        from services.prompt_store.domain.notifications.service import NotificationsService

        prompt_service = PromptService()
        bulk_service = BulkOperationService()
        notifications_service = NotificationsService()

        # Register webhook for bulk operation events
        webhook_result = notifications_service.register_webhook({
            "name": "bulk_test_webhook",
            "url": "https://httpbin.org/post",
            "events": ["bulk_operation.started", "bulk_operation.completed"],
            "is_active": True,
            "created_by": "integration_test"
        })

        # Create multiple prompts for bulk operation
        prompt_ids = []
        for i in range(5):
            prompt = prompt_service.create_entity({
                "name": f"bulk_test_prompt_{i}",
                "category": "bulk_test",
                "content": f"Content for bulk test prompt {i}",
                "created_by": "integration_test"
            })
            prompt_ids.append(prompt.id)

        # Execute bulk operation (this would normally update all prompts)
        # For this test, we'll just create the operation record
        bulk_result = bulk_service.create_bulk_operation_sync({
            "operation_type": "update_prompts",
            "total_items": len(prompt_ids),
            "created_by": "integration_test",
            "metadata": {"prompt_ids": prompt_ids}
        })

        assert bulk_result["operation_type"] == "update_prompts"
        assert bulk_result["total_items"] == 5

        # Check operation status
        status = bulk_service.get_operation_status(bulk_result["id"])
        assert status["operation_id"] == bulk_result["id"]
        assert status["status"] == "pending"


@pytest.mark.integration
@pytest.mark.prompt_store
class TestRefinementWorkflow:
    """Test LLM-assisted prompt refinement workflow."""

    @pytest.mark.asyncio
    async def test_refinement_workflow_with_notifications(self, prompt_store_db):
        """Test complete refinement workflow with notifications."""
        from services.prompt_store.domain.prompts.service import PromptService
        from services.prompt_store.domain.refinement.service import PromptRefinementService
        from services.prompt_store.domain.notifications.service import NotificationsService

        prompt_service = PromptService()
        refinement_service = PromptRefinementService()
        notifications_service = NotificationsService()

        # Register webhook for refinement events
        webhook_result = notifications_service.register_webhook({
            "name": "refinement_test_webhook",
            "url": "https://httpbin.org/post",
            "events": ["refinement.started", "refinement.completed"],
            "is_active": True,
            "created_by": "integration_test"
        })

        # Create a prompt to refine
        prompt = prompt_service.create_entity({
            "name": "refinement_test_prompt",
            "category": "refinement_test",
            "content": "This is a prompt that needs improvement",
            "created_by": "integration_test"
        })

        # Start refinement process (mock the LLM call)
        with pytest.mock.patch.object(refinement_service, '_call_llm_service') as mock_llm, \
             pytest.mock.patch.object(refinement_service, '_store_refinement_result') as mock_store:

            mock_llm.return_value = {"refined_content": "This is an improved version of the prompt"}
            mock_store.return_value = "doc_123"

            result = await refinement_service.refine_prompt(
                prompt.id,
                "Make this prompt more specific and actionable",
                "interpreter",
                None,
                "integration_test"
            )

            assert result["session_id"] is not None
            assert result["status"] == "processing"
            mock_llm.assert_called_once()
            mock_store.assert_called_once()

        # Get refinement status
        status = refinement_service.get_refinement_status(result["session_id"])
        assert status["id"] == result["session_id"]
        assert status["status"] == "completed"

        # Get refinement history
        history = refinement_service.get_refinement_history(prompt.id)
        assert history["prompt_id"] == prompt.id
        assert len(history["refinement_sessions"]) >= 1


@pytest.mark.integration
@pytest.mark.prompt_store
class TestCrossDomainAnalytics:
    """Test analytics across multiple domains."""

    def test_comprehensive_analytics_workflow(self, prompt_store_db):
        """Test analytics collection across all domains."""
        from services.prompt_store.domain.prompts.service import PromptService
        from services.prompt_store.domain.lifecycle.service import LifecycleService
        from services.prompt_store.domain.relationships.service import RelationshipsService
        from services.prompt_store.domain.analytics.service import AnalyticsService
        from services.prompt_store.domain.ab_testing.service import ABTestService

        # Initialize all services
        prompt_service = PromptService()
        lifecycle_service = LifecycleService()
        relationships_service = RelationshipsService()
        analytics_service = AnalyticsService()
        ab_test_service = ABTestService()

        # Create comprehensive test data
        prompts = []
        for i in range(3):
            prompt = prompt_service.create_entity({
                "name": f"analytics_test_prompt_{i}",
                "category": "analytics_test",
                "content": f"Content for analytics test prompt {i}",
                "created_by": "integration_test"
            })
            prompts.append(prompt)

        # Update lifecycles
        lifecycle_service.update_lifecycle_status(
            prompts[0].id, "published", "Publishing for analytics", "integration_test"
        )
        lifecycle_service.update_lifecycle_status(
            prompts[1].id, "deprecated", "Deprecating for analytics", "integration_test"
        )

        # Create relationships
        relationships_service.create_relationship(
            prompts[0].id,
            {
                "target_prompt_id": prompts[1].id,
                "relationship_type": "extends",
                "strength": 0.8
            },
            "integration_test"
        )

        # Create A/B test
        ab_test_service.create_ab_test({
            "name": "analytics_ab_test",
            "prompt_a_id": prompts[0].id,
            "prompt_b_id": prompts[2].id,
            "traffic_percentage": 50,
            "created_by": "integration_test"
        })

        # Get comprehensive analytics
        summary_stats = analytics_service.get_summary_stats()

        # Verify analytics capture all activities
        assert summary_stats["total_prompts"] >= 3
        assert "top_performing_prompts" in summary_stats
        assert "recent_activity" in summary_stats

        # Check individual prompt analytics
        for prompt in prompts:
            prompt_analytics = analytics_service.get_prompt_analytics(prompt.id)
            assert prompt_analytics["prompt_id"] == prompt.id
            assert "performance_metrics" in prompt_analytics

        # Verify data consistency across domains
        lifecycle_counts = lifecycle_service.get_status_counts()
        assert lifecycle_counts["status_counts"]["published"] >= 1
        assert lifecycle_counts["status_counts"]["deprecated"] >= 1


@pytest.mark.integration
@pytest.mark.prompt_store
class TestNotificationEventSystem:
    """Test the complete notification event system."""

    @pytest.mark.asyncio
    async def test_event_driven_notifications(self, prompt_store_db):
        """Test that domain operations trigger appropriate notifications."""
        from services.prompt_store.domain.prompts.service import PromptService
        from services.prompt_store.domain.lifecycle.service import LifecycleService
        from services.prompt_store.domain.notifications.service import NotificationsService

        prompt_service = PromptService()
        lifecycle_service = LifecycleService()
        notifications_service = NotificationsService()

        # Register webhooks for different events
        webhook_results = []
        events_to_monitor = [
            "prompt.created",
            "prompt.lifecycle_changed",
            "prompt.updated"
        ]

        for event in events_to_monitor:
            webhook = notifications_service.register_webhook({
                "name": f"event_test_webhook_{event}",
                "url": "https://httpbin.org/post",
                "events": [event],
                "is_active": True,
                "created_by": "integration_test"
            })
            webhook_results.append(webhook)

        # Perform operations that should trigger notifications
        # 1. Create prompt (should trigger prompt.created)
        prompt = prompt_service.create_entity({
            "name": "notification_test_prompt",
            "category": "notification_test",
            "content": "Content for notification testing",
            "created_by": "integration_test"
        })

        # 2. Update lifecycle (should trigger prompt.lifecycle_changed)
        await lifecycle_service.update_lifecycle_status(
            prompt.id, "published", "Testing notifications", "integration_test"
        )

        # 3. Update prompt content (should trigger prompt.updated)
        updated_prompt = prompt_service.update_entity(prompt.id, {"content": "Updated content"})
        assert updated_prompt.content == "Updated content"

        # Check that notifications were created
        notification_stats = notifications_service.get_notification_stats()
        assert notification_stats["total_notifications"] >= 3  # created + lifecycle + updated

        # Verify event types were captured
        event_counts = notification_stats["event_counts"]
        assert event_counts.get("prompt.created", 0) >= 1
        assert event_counts.get("prompt.lifecycle_changed", 0) >= 1
        assert event_counts.get("prompt.updated", 0) >= 1
