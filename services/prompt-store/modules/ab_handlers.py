"""A/B testing handlers for Prompt Store service.

Handles the complex logic for A/B testing endpoints.
"""
from typing import Dict, Any

from .shared_utils import (
    get_prompt_store_client,
    handle_prompt_error,
    create_prompt_success_response,
    build_prompt_context
)
from services.shared.constants_new import ErrorCodes


class ABHandlers:
    """Handles A/B testing operations."""

    @staticmethod
    async def handle_create_ab_test(test_data) -> Dict[str, Any]:
        """Create A/B test."""
        try:
            db = get_prompt_store_client()
            result = await ABHandlers._create_ab_test_logic(test_data, db)

            context = build_prompt_context("ab_test_create", test_name=getattr(test_data, 'name', None))
            return create_prompt_success_response("A/B test created", result, **context)

        except Exception as e:
            context = build_prompt_context("ab_test_create")
            return handle_prompt_error("create A/B test", e, **context)

    @staticmethod
    async def handle_select_prompt_for_test(test_id: str) -> Dict[str, Any]:
        """Select prompt for A/B testing."""
        try:
            db = get_prompt_store_client()
            prompt_id = await ABHandlers._select_prompt_for_test_logic(test_id, db)

            if not prompt_id:
                return handle_prompt_error(
                    "find",
                    Exception(f"A/B test '{test_id}' not found"),
                    ErrorCodes.AB_TEST_NOT_FOUND,
                    test_id=test_id
                )

            result = {"prompt_id": prompt_id}
            context = build_prompt_context("ab_test_select", test_id=test_id, prompt_id=prompt_id)
            return create_prompt_success_response("selected for A/B testing", result, **context)

        except Exception as e:
            context = build_prompt_context("ab_test_select", test_id=test_id)
            return handle_prompt_error("select for A/B testing", e, **context)

    @staticmethod
    async def _create_ab_test_logic(test_data, db) -> Dict[str, Any]:
        """Create A/B test logic with enhanced validation and transaction safety."""
        from ..models import ABTest

        # Validate test data
        if not hasattr(test_data, 'prompt_a_id') or not hasattr(test_data, 'prompt_b_id'):
            raise Exception("A/B test requires both prompt_a_id and prompt_b_id")

        # Check if prompts exist
        prompt_a = db.get_prompt(test_data.prompt_a_id)
        prompt_b = db.get_prompt(test_data.prompt_b_id)

        if not prompt_a or not prompt_b:
            missing_ids = []
            if not prompt_a:
                missing_ids.append(test_data.prompt_a_id)
            if not prompt_b:
                missing_ids.append(test_data.prompt_b_id)

            raise Exception(f"Prompts not found: {', '.join(missing_ids)}")

        # Create test object
        test = ABTest(
            name=test_data.name,
            description=getattr(test_data, 'description', ""),
            prompt_a_id=test_data.prompt_a_id,
            prompt_b_id=test_data.prompt_b_id,
            test_metric=getattr(test_data, 'test_metric', 'response_quality'),
            traffic_split=getattr(test_data, 'traffic_split', 0.5),
            target_audience=getattr(test_data, 'target_audience', None),
            created_by="api_user"
        )

        # Save to database
        created_test = db.create_ab_test(test)

        return {
            "test_id": created_test.id,
            "name": created_test.name,
            "prompt_a_id": created_test.prompt_a_id,
            "prompt_b_id": created_test.prompt_b_id,
            "status": "active" if created_test.is_active else "inactive"
        }

    @staticmethod
    async def _select_prompt_for_test_logic(test_id: str, db) -> str:
        """Select prompt for A/B testing logic."""
        return db.select_prompt_for_test(test_id)


# Create singleton instance
ab_handlers = ABHandlers()
