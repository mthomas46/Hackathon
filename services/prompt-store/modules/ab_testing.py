"""A/B Testing functionality for the Prompt Store service.

This module contains all A/B testing operations and logic,
extracted from the main prompt store service to improve maintainability.
"""

from typing import Dict, Any
from services.shared.monitoring.logging import fire_and_forget
from services.shared.core.constants_new import ErrorCodes
from services.shared.core.responses.responses import create_error_response

# Import shared utilities for consistency
from .shared_utils import handle_prompt_error, create_prompt_success_response, build_prompt_context


def create_ab_test(test_data, db):
    """Create A/B test logic with enhanced validation and transaction safety."""
    from .shared_utils import build_prompt_context

    context = build_prompt_context("create_ab_test", test_name=getattr(test_data, 'name', None))

    try:
        # Import models here to avoid circular imports
        from ..models import ABTest

        # Validate test data
        if not hasattr(test_data, 'prompt_a_id') or not hasattr(test_data, 'prompt_b_id'):
            return handle_prompt_error(
                "create A/B test",
                Exception("A/B test requires both prompt_a_id and prompt_b_id"),
                **context
            )

        # Check if prompts exist
        prompt_a = db.get_prompt(test_data.prompt_a_id)
        prompt_b = db.get_prompt(test_data.prompt_b_id)

        if not prompt_a or not prompt_b:
            missing_ids = []
            if not prompt_a:
                missing_ids.append(test_data.prompt_a_id)
            if not prompt_b:
                missing_ids.append(test_data.prompt_b_id)

            return handle_prompt_error(
                "create A/B test",
                Exception(f"Prompts not found: {', '.join(missing_ids)}"),
                prompt_ids=missing_ids,
                **context
            )

        test = ABTest(
            name=test_data.name,
            description=getattr(test_data, 'description', "") or "",
            prompt_a_id=test_data.prompt_a_id,
            prompt_b_id=test_data.prompt_b_id,
            test_metric=getattr(test_data, 'test_metric', None) or "response_quality",
            traffic_split=getattr(test_data, 'traffic_split', None) or 0.5,
            created_by="api_user"
        )

        created = db.create_ab_test(test)

        context = build_prompt_context("ab_test_create", test_id=created.id, test_name=created.name)
        return create_prompt_success_response("A/B test created", {
            "id": created.id,
            "name": created.name,
            "status": "created"
        }, **context)

    except Exception as e:
        context = build_prompt_context("ab_test_create", test_name=getattr(test_data, 'name', None))
        return handle_prompt_error("create A/B test", e, **context)


def select_prompt_for_test(test_id: str, db):
    """Select prompt for A/B testing logic with enhanced validation."""
    context = build_prompt_context("select_prompt_for_test", test_id=test_id)

    try:
        if not test_id:
            return handle_prompt_error(
                "select prompt for test",
                Exception("Test ID is required"),
                **context
            )

        prompt_id = db.select_prompt_for_test(test_id)

        if not prompt_id:
            return handle_prompt_error(
                "find A/B test",
                Exception(f"A/B test '{test_id}' not found or inactive"),
                test_id=test_id,
                **context
            )

        context = build_prompt_context("ab_test_select", test_id=test_id, prompt_id=prompt_id)
        return create_prompt_success_response("selected", {"prompt_id": prompt_id}, **context)

    except Exception as e:
        context = build_prompt_context("ab_test_select", test_id=test_id)
        return handle_prompt_error("select prompt for A/B testing", e, **context)


def get_usage_analytics(db):
    """Get usage analytics data with comprehensive metrics."""
    context = build_prompt_context("get_usage_analytics")

    try:
        # Get actual usage statistics from database
        usage_stats = db.get_usage_stats(days=7)  # Last 7 days

        # Get total prompts count
        total_prompts = db.get_total_prompts()

        # Get prompt analytics for performance metrics
        analytics_data = {
            "total_prompts": total_prompts,
            "total_usage": usage_stats.get('total_usage', 0),
            "success_rate": usage_stats.get('success_rate', 0.0),
            "popular_categories": usage_stats.get('top_prompts', []),
            "performance_metrics": {
                "avg_response_time": usage_stats.get('avg_response_time', 0),
                "success_rate": usage_stats.get('success_rate', 0),
                "usage_trends": [],  # Would be calculated from historical data
                "total_requests": usage_stats.get('total_requests', 0)
            }
        }

        context = build_prompt_context("analytics_retrieval", total_prompts=total_prompts)
        return create_prompt_success_response("analytics retrieved", analytics_data, **context)

    except Exception as e:
        context = build_prompt_context("analytics_retrieval")
        return handle_prompt_error("retrieve analytics", e, **context)
