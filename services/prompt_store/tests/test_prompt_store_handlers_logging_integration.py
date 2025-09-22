"""Tests for Prompt Store Additional Handlers logging integration with LogCollectorClient."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestPromptStoreHandlersLoggingIntegration:
    """Test Prompt Store additional handlers logging integration with LogCollectorClient."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_logger_client(self):
        """Mock LogCollectorClient."""
        mock_client = AsyncMock(spec=LogCollectorClient)
        return mock_client

    @pytest.fixture(autouse=True)
    async def setup_logger_client(self, mock_logger_client):
        """Setup mock logger client for all tests."""
        # Patch the get_logger_client function in both A/B testing and analytics handlers
        with patch("services.prompt_store.domain.ab_testing.handlers.get_logger_client") as mock_ab_get_client, patch(
            "services.prompt_store.domain.analytics.handlers.get_logger_client"
        ) as mock_analytics_get_client:

            mock_ab_get_client.return_value = mock_logger_client
            mock_analytics_get_client.return_value = mock_logger_client
            yield

    @pytest.mark.asyncio
    async def test_ab_test_creation_logging_success(self, client, mock_logger_client):
        """Test A/B test creation endpoint logging on success."""
        mock_ab_test = {
            "test_id": "ab_test_12345",
            "name": "Test A/B Test",
            "description": "Testing prompt variants",
            "prompt_variants": [
                {"id": "variant_a", "prompt_id": "prompt1", "weight": 50},
                {"id": "variant_b", "prompt_id": "prompt2", "weight": 50},
            ],
            "target_metric": "response_quality",
            "traffic_distribution": "even",
            "duration_days": 14,
            "status": "active",
        }

        with patch("services.prompt_store.domain.ab_testing.handlers.ABTestService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_ab_test.return_value = mock_ab_test
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers

            handler = ABTestHandlers()

            ab_test_data = {
                "name": "Test A/B Test",
                "description": "Testing prompt variants",
                "prompt_variants": [
                    {"id": "variant_a", "prompt_id": "prompt1", "weight": 50},
                    {"id": "variant_b", "prompt_id": "prompt2", "weight": 50},
                ],
                "target_metric": "response_quality",
                "traffic_distribution": "even",
                "duration_days": 14,
            }

            result = await handler.handle_create_ab_test(ab_test_data)

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and created
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check A/B test creation events
            business_calls = mock_logger_client.log_business_event.call_args_list
            creation_started = next((call for call in business_calls if call[0][0] == "ab_test_creation_started"), None)
            test_created = next((call for call in business_calls if call[0][0] == "ab_test_created"), None)

            assert creation_started is not None
            assert test_created is not None

            started_data = creation_started[0][1]
            assert started_data["test_name"] == "Test A/B Test"
            assert started_data["prompt_variants_count"] == 2
            assert started_data["target_metric"] == "response_quality"
            assert started_data["traffic_distribution"] == "even"
            assert started_data["duration_days"] == 14

            created_data = test_created[0][1]
            assert created_data["test_id"] == "ab_test_12345"
            assert created_data["success"] is True
            assert created_data["variants_configured"] == 2
            assert created_data["experiment_ready"] is True

    @pytest.mark.asyncio
    async def test_ab_test_prompt_selection_logging_success(self, client, mock_logger_client):
        """Test A/B test prompt selection endpoint logging on success."""
        mock_selection_result = {
            "variant_id": "variant_a",
            "prompt_id": "prompt1",
            "test_id": "ab_test_12345",
            "user_id": "user123",
            "session_id": "session_abc",
        }

        with patch("services.prompt_store.domain.ab_testing.handlers.ABTestService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.select_prompt_for_test.return_value = mock_selection_result
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers

            handler = ABTestHandlers()

            result = await handler.handle_select_prompt_for_test(
                test_id="ab_test_12345", user_id="user123", session_id="session_abc"
            )

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and selected
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check prompt selection events
            business_calls = mock_logger_client.log_business_event.call_args_list
            selection_started = next(
                (call for call in business_calls if call[0][0] == "ab_test_prompt_selection_started"), None
            )
            prompt_selected = next((call for call in business_calls if call[0][0] == "ab_test_prompt_selected"), None)

            assert selection_started is not None
            assert prompt_selected is not None

            started_data = selection_started[0][1]
            assert started_data["test_id"] == "ab_test_12345"
            assert started_data["user_id"] == "user123"
            assert started_data["session_id"] == "session_abc"
            assert started_data["user_targeted"] is True
            assert started_data["session_tracked"] is True

            selected_data = prompt_selected[0][1]
            assert selected_data["test_id"] == "ab_test_12345"
            assert selected_data["variant_id"] == "variant_a"
            assert selected_data["success"] is True
            assert selected_data["experiment_participation"] is True

    @pytest.mark.asyncio
    async def test_usage_metrics_recording_logging_success(self, client, mock_logger_client):
        """Test usage metrics recording endpoint logging on success."""
        usage_data = {
            "tokens_used": 150,
            "response_time_ms": 2500,
            "error_count": 0,
            "success_rate": 1.0,
            "llm_provider": "openai",
            "model": "gpt-4",
        }

        with patch("services.prompt_store.domain.analytics.handlers.AnalyticsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.record_usage_metrics.return_value = None
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers

            handler = AnalyticsHandlers()

            result = await handler.handle_record_usage_metrics(
                prompt_id="prompt_12345", version=2, usage_data=usage_data
            )

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and recorded
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check usage metrics recording events
            business_calls = mock_logger_client.log_business_event.call_args_list
            recording_started = next(
                (call for call in business_calls if call[0][0] == "usage_metrics_recording_started"), None
            )
            metrics_recorded = next((call for call in business_calls if call[0][0] == "usage_metrics_recorded"), None)

            assert recording_started is not None
            assert metrics_recorded is not None

            started_data = recording_started[0][1]
            assert started_data["prompt_id"] == "prompt_12345"
            assert started_data["prompt_version"] == 2
            assert started_data["metrics_keys_count"] == 6
            assert started_data["performance_data_collection"] is True

            recorded_data = metrics_recorded[0][1]
            assert recorded_data["prompt_id"] == "prompt_12345"
            assert recorded_data["prompt_version"] == 2
            assert recorded_data["success"] is True
            assert recorded_data["metrics_persisted"] is True
            assert recorded_data["analytics_pipeline_updated"] is True

    @pytest.mark.asyncio
    async def test_analytics_dashboard_logging_success(self, client, mock_logger_client):
        """Test analytics dashboard endpoint logging on success."""
        mock_dashboard = {
            "total_prompts": 25,
            "total_usage": 15000,
            "average_response_time": 2400,
            "top_performing_prompts": ["prompt1", "prompt2"],
            "usage_trends": {"last_7_days": 1200, "last_30_days": 4800},
            "satisfaction_scores": {"average": 4.2, "distribution": [10, 20, 30, 25, 15]},
        }

        with patch("services.prompt_store.domain.analytics.handlers.AnalyticsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_analytics_dashboard.return_value = mock_dashboard
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers

            handler = AnalyticsHandlers()

            result = await handler.handle_get_analytics_dashboard(time_range_days=30)

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check analytics dashboard events
            business_calls = mock_logger_client.log_business_event.call_args_list
            retrieval_started = next(
                (call for call in business_calls if call[0][0] == "analytics_dashboard_retrieval_started"), None
            )
            dashboard_retrieved = next(
                (call for call in business_calls if call[0][0] == "analytics_dashboard_retrieved"), None
            )

            assert retrieval_started is not None
            assert dashboard_retrieved is not None

            started_data = retrieval_started[0][1]
            assert started_data["time_range_days"] == 30
            assert started_data["analytics_scope"] == "comprehensive_dashboard"
            assert started_data["performance_insights_requested"] is True
            assert started_data["data_aggregation_required"] is True

            retrieved_data = dashboard_retrieved[0][1]
            assert retrieved_data["time_range_days"] == 30
            assert retrieved_data["success"] is True
            assert retrieved_data["dashboard_data_points"] == 6
            assert retrieved_data["performance_insights_generated"] is True
            assert retrieved_data["analytics_computation_complete"] is True

    @pytest.mark.asyncio
    async def test_ab_test_creation_logging_validation_failure(self, client, mock_logger_client):
        """Test A/B test creation endpoint logging on validation failure."""
        with patch("services.prompt_store.domain.ab_testing.handlers.ABTestService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_ab_test.side_effect = ValueError("Invalid traffic distribution")
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers

            handler = ABTestHandlers()

            ab_test_data = {
                "name": "Invalid Test",
                "description": "Invalid configuration",
                "prompt_variants": [],
                "target_metric": "invalid_metric",
                "traffic_distribution": "invalid",
                "duration_days": 0,
            }

            result = await handler.handle_create_ab_test(ab_test_data)

            # Verify error logging
            business_calls = mock_logger_client.log_business_event.call_args_list
            validation_failed = next(
                (call for call in business_calls if call[0][0] == "ab_test_creation_validation_failed"), None
            )
            assert validation_failed is not None

            failed_data = validation_failed[0][1]
            assert failed_data["test_name"] == "Invalid Test"
            assert failed_data["error_type"] == "validation_error"
            assert "Invalid traffic distribution" in failed_data["error_message"]
            assert failed_data["configuration_validation_failed"] is True

    @pytest.mark.asyncio
    async def test_ab_test_prompt_selection_logging_test_not_found(self, client, mock_logger_client):
        """Test A/B test prompt selection endpoint logging when test not found."""
        with patch("services.prompt_store.domain.ab_testing.handlers.ABTestService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.select_prompt_for_test.return_value = None  # Test not found
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers

            handler = ABTestHandlers()

            result = await handler.handle_select_prompt_for_test(test_id="nonexistent_test", user_id="user123")

            # Verify logging calls for test not found
            business_calls = mock_logger_client.log_business_event.call_args_list
            test_not_found = next((call for call in business_calls if call[0][0] == "ab_test_not_found"), None)
            assert test_not_found is not None

            not_found_data = test_not_found[0][1]
            assert not_found_data["test_id"] == "nonexistent_test"
            assert not_found_data["result_status"] == "test_inactive_or_missing"
            assert not_found_data["variant_selection_failed"] is True

    @pytest.mark.asyncio
    async def test_usage_metrics_recording_logging_failure(self, client, mock_logger_client):
        """Test usage metrics recording endpoint logging on failure."""
        usage_data = {"tokens_used": 150, "response_time_ms": 2500}

        with patch("services.prompt_store.domain.analytics.handlers.AnalyticsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.record_usage_metrics.side_effect = Exception("Database connection failed")
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers

            handler = AnalyticsHandlers()

            result = await handler.handle_record_usage_metrics(
                prompt_id="prompt_12345", version=2, usage_data=usage_data
            )

            # Verify error logging
            assert mock_logger_client.log_error.call_count == 1
            business_calls = mock_logger_client.log_business_event.call_args_list
            recording_failed = next(
                (call for call in business_calls if call[0][0] == "usage_metrics_recording_failed"), None
            )
            assert recording_failed is not None

            failed_data = recording_failed[0][1]
            assert failed_data["prompt_id"] == "prompt_12345"
            assert failed_data["prompt_version"] == 2
            assert failed_data["error_type"] == "Exception"
            assert "Database connection failed" in failed_data["error_message"]

    @pytest.mark.asyncio
    async def test_analytics_dashboard_logging_failure(self, client, mock_logger_client):
        """Test analytics dashboard endpoint logging on failure."""
        with patch("services.prompt_store.domain.analytics.handlers.AnalyticsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_analytics_dashboard.side_effect = Exception("Analytics computation failed")
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers

            handler = AnalyticsHandlers()

            result = await handler.handle_get_analytics_dashboard(time_range_days=7)

            # Verify error logging
            assert mock_logger_client.log_error.call_count == 1
            business_calls = mock_logger_client.log_business_event.call_args_list
            retrieval_failed = next(
                (call for call in business_calls if call[0][0] == "analytics_dashboard_retrieval_failed"), None
            )
            assert retrieval_failed is not None

            failed_data = retrieval_failed[0][1]
            assert failed_data["time_range_days"] == 7
            assert failed_data["error_type"] == "Exception"
            assert "Analytics computation failed" in failed_data["error_message"]

    @pytest.mark.asyncio
    async def test_request_ids_generated_uniquely(self, mock_logger_client):
        """Test that all prompt store handlers generate unique request IDs."""
        request_ids = set()

        # Test multiple handler methods
        with patch("services.prompt_store.domain.ab_testing.handlers.ABTestService") as mock_ab_service_class, patch(
            "services.prompt_store.domain.analytics.handlers.AnalyticsService"
        ) as mock_analytics_service_class:

            mock_ab_service = MagicMock()
            mock_ab_service.create_ab_test.return_value = {"test_id": "test"}
            mock_ab_service.select_prompt_for_test.return_value = {"variant_id": "variant_a"}
            mock_ab_service_class.return_value = mock_ab_service

            mock_analytics_service = MagicMock()
            mock_analytics_service.record_usage_metrics.return_value = None
            mock_analytics_service.get_analytics_dashboard.return_value = {"data": "test"}
            mock_analytics_service_class.return_value = mock_analytics_service

            # Test A/B testing handlers
            from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers

            ab_handler = ABTestHandlers()

            await ab_handler.handle_create_ab_test({"name": "Test", "prompt_variants": [], "target_metric": "test"})
            await ab_handler.handle_select_prompt_for_test("test123")

            # Test analytics handlers
            from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers

            analytics_handler = AnalyticsHandlers()

            await analytics_handler.handle_record_usage_metrics("prompt123", 1, {"tokens": 100})
            await analytics_handler.handle_get_analytics_dashboard(30)

            # Collect request IDs from business events
            business_calls = mock_logger_client.log_business_event.call_args_list
            for call in business_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get("request_id")
                    if request_id:
                        request_ids.add(request_id)

        # Should have collected multiple unique request IDs
        assert len(request_ids) >= 4  # At least one per handler method

        # All request IDs should follow expected patterns
        for request_id in request_ids:
            assert any(
                prefix in request_id
                for prefix in ["ab_test_create_", "ab_test_select_", "usage_metrics_record_", "analytics_dashboard_"]
            )

    @pytest.mark.asyncio
    async def test_performance_metrics_accuracy(self, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        with patch("services.prompt_store.domain.analytics.handlers.AnalyticsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.record_usage_metrics.return_value = None
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers

            handler = AnalyticsHandlers()

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            result = await handler.handle_record_usage_metrics(
                prompt_id="prompt123", version=1, usage_data={"tokens_used": 100}
            )

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            metrics_perf = next((call for call in perf_calls if call[0][0] == "usage_metrics_recording"), None)
            assert metrics_perf is not None

            processing_time = metrics_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self):
        """Test graceful handling when logging is disabled."""
        # Patch get_logger_client to return None
        with patch("services.prompt_store.domain.ab_testing.handlers.get_logger_client") as mock_ab_get_client, patch(
            "services.prompt_store.domain.analytics.handlers.get_logger_client"
        ) as mock_analytics_get_client:

            mock_ab_get_client.return_value = None
            mock_analytics_get_client.return_value = None

            with patch(
                "services.prompt_store.domain.ab_testing.handlers.ABTestService"
            ) as mock_ab_service_class, patch(
                "services.prompt_store.domain.analytics.handlers.AnalyticsService"
            ) as mock_analytics_service_class:

                mock_ab_service = MagicMock()
                mock_ab_service.select_prompt_for_test.return_value = {"variant_id": "test"}
                mock_ab_service_class.return_value = mock_ab_service

                mock_analytics_service = MagicMock()
                mock_analytics_service.get_analytics_dashboard.return_value = {"test": "data"}
                mock_analytics_service_class.return_value = mock_analytics_service

                # Test A/B testing handler
                from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers

                ab_handler = ABTestHandlers()
                result = await ab_handler.handle_select_prompt_for_test("test123")
                assert result["status"] == "success"  # Should still work without logging

                # Test analytics handler
                from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers

                analytics_handler = AnalyticsHandlers()
                result = await analytics_handler.handle_get_analytics_dashboard(7)
                assert result["status"] == "success"  # Should still work without logging

    @pytest.mark.asyncio
    async def test_business_events_comprehensive_coverage(self, mock_logger_client):
        """Test that all major business events are logged across prompt store handlers."""
        expected_events = {
            # A/B testing events
            "ab_test_creation_started",
            "ab_test_created",
            "ab_test_creation_validation_failed",
            "ab_test_creation_failed",
            "ab_test_prompt_selection_started",
            "ab_test_prompt_selected",
            "ab_test_not_found",
            "ab_test_prompt_selection_failed",
            # Analytics events
            "usage_metrics_recording_started",
            "usage_metrics_recorded",
            "usage_metrics_recording_failed",
            "analytics_dashboard_retrieval_started",
            "analytics_dashboard_retrieved",
            "analytics_dashboard_retrieval_failed",
        }

        # Test representative methods from each handler
        with patch("services.prompt_store.domain.ab_testing.handlers.ABTestService") as mock_ab_service_class, patch(
            "services.prompt_store.domain.analytics.handlers.AnalyticsService"
        ) as mock_analytics_service_class:

            mock_ab_service = MagicMock()
            mock_ab_service.create_ab_test.return_value = {"test_id": "test"}
            mock_ab_service.select_prompt_for_test.return_value = {"variant_id": "variant_a"}
            mock_ab_service_class.return_value = mock_ab_service

            mock_analytics_service = MagicMock()
            mock_analytics_service.record_usage_metrics.return_value = None
            mock_analytics_service.get_analytics_dashboard.return_value = {"data": "test"}
            mock_analytics_service_class.return_value = mock_analytics_service

            # Test A/B testing handler methods
            from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers

            ab_handler = ABTestHandlers()

            await ab_handler.handle_create_ab_test(
                {"name": "Test", "prompt_variants": [{"id": "v1", "prompt_id": "p1", "weight": 100}]}
            )
            await ab_handler.handle_select_prompt_for_test("test123")

            # Test analytics handler methods
            from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers

            analytics_handler = AnalyticsHandlers()

            await analytics_handler.handle_record_usage_metrics("prompt123", 1, {"tokens": 100})
            await analytics_handler.handle_get_analytics_dashboard(30)

            # Check which events were actually logged
            business_calls = mock_logger_client.log_business_event.call_args_list
            logged_events = {call[0][0] for call in business_calls}

            # Verify we logged key events (not all, as some require specific error conditions)
            key_events_logged = logged_events.intersection(
                {
                    "ab_test_creation_started",
                    "ab_test_created",
                    "ab_test_prompt_selection_started",
                    "ab_test_prompt_selected",
                    "usage_metrics_recording_started",
                    "usage_metrics_recorded",
                    "analytics_dashboard_retrieval_started",
                    "analytics_dashboard_retrieved",
                }
            )

            assert len(key_events_logged) >= 8  # Should have logged most key events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
