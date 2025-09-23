"""Tests for Orchestrator Reporting Routes logging integration with
LogCollectorClient."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestOrchestratorReportingLoggingIntegration:
    """Test Orchestrator Reporting routes logging integration with
    LogCollectorClient."""

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
        # Patch the get_logger_client function in the reporting routes
        with patch("services.orchestrator.presentation.api.reporting.routes.get_logger_client") as mock_get_client:
            mock_get_client.return_value = mock_logger_client
            yield

    @pytest.mark.asyncio
    async def test_report_generation_logging_success(self, client, mock_logger_client):
        """Test report generation endpoint logging on success."""
        mock_result = {
            "report_id": "report_12345",
            "status": "completed",
            "format": "pdf",
            "size_bytes": 1024000,
            "generation_time_ms": 2500,
            "charts_included": True,
        }

        with patch("services.orchestrator.presentation.api.reporting.routes.container") as mock_container:
            mock_container.generate_report_use_case.execute.return_value = mock_result

            report_request = {
                "report_type": "pr_confidence",
                "parameters": {"repository": "test/repo", "confidence_threshold": 0.8},
                "filters": {"status": "completed"},
                "date_range": {"start": "2024-01-01", "end": "2024-01-31"},
                "format": "pdf",
                "include_charts": True,
            }
            response = client.post("/api/v1/reporting/generate", json=report_request)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and completed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check report generation events
            business_calls = mock_logger_client.log_business_event.call_args_list
            generation_started = next(
                (call for call in business_calls if call[0][0] == "report_generation_started"), None
            )
            generation_completed = next(
                (call for call in business_calls if call[0][0] == "report_generation_completed"), None
            )

            assert generation_started is not None
            assert generation_completed is not None

            started_data = generation_started[0][1]
            assert started_data["report_type"] == "pr_confidence"
            assert started_data["parameters_count"] == 2
            assert started_data["filters_applied"] is True
            assert started_data["date_range_specified"] is True
            assert started_data["output_format"] == "pdf"
            assert started_data["charts_included"] is True

            completed_data = generation_completed[0][1]
            assert completed_data["report_id"] == "report_12345"
            assert completed_data["success"] is True
            assert completed_data["report_type"] == "pr_confidence"
            assert completed_data["output_format"] == "pdf"
            assert completed_data["charts_generated"] is True

    @pytest.mark.asyncio
    async def test_report_retrieval_logging_success(self, client, mock_logger_client):
        """Test report retrieval endpoint logging on success."""
        report_id = "report_12345"
        mock_result = {
            "report_id": report_id,
            "report_type": "pr_confidence",
            "status": "completed",
            "format": "pdf",
            "size_bytes": 2048000,
            "generated_at": "2024-01-15T10:30:00Z",
            "parameters": {"repository": "test/repo"},
            "data": {"summary": "Test report data"},
        }

        with patch("services.orchestrator.presentation.api.reporting.routes.container") as mock_container:
            mock_container.get_report_use_case.execute.return_value = mock_result

            response = client.get(f"/api/v1/reporting/reports/{report_id}")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check report retrieval events
            business_calls = mock_logger_client.log_business_event.call_args_list
            retrieval_started = next(
                (call for call in business_calls if call[0][0] == "report_retrieval_started"), None
            )
            report_retrieved = next((call for call in business_calls if call[0][0] == "report_retrieved"), None)

            assert retrieval_started is not None
            assert report_retrieved is not None

            started_data = retrieval_started[0][1]
            assert started_data["report_id"] == report_id
            assert started_data["data_scope"] == "stored_report"
            assert started_data["report_cache_access"] is True

            retrieved_data = report_retrieved[0][1]
            assert retrieved_data["report_id"] == report_id
            assert retrieved_data["success"] is True
            assert retrieved_data["cache_hit"] is True
            assert retrieved_data["report_format"] == "pdf"

    @pytest.mark.asyncio
    async def test_report_retrieval_logging_not_found(self, client, mock_logger_client):
        """Test report retrieval endpoint logging when report not found."""
        report_id = "nonexistent_report"

        with patch("services.orchestrator.presentation.api.reporting.routes.container") as mock_container:
            mock_container.get_report_use_case.execute.return_value = None

            response = client.get(f"/api/v1/reporting/reports/{report_id}")
            assert response.status_code == 404

            # Verify logging calls
            business_calls = mock_logger_client.log_business_event.call_args_list
            report_not_found = next((call for call in business_calls if call[0][0] == "report_not_found"), None)
            assert report_not_found is not None

            not_found_data = report_not_found[0][1]
            assert not_found_data["report_id"] == report_id
            assert not_found_data["result_status"] == "not_found"
            assert not_found_data["cache_miss"] is True

    @pytest.mark.asyncio
    async def test_reports_listing_logging_with_filters(self, client, mock_logger_client):
        """Test reports listing endpoint logging with various filters."""
        mock_result = type(
            "MockResult",
            (),
            {
                "reports": [
                    {"report_id": "r1", "report_type": "pr_confidence", "status": "completed"},
                    {"report_id": "r2", "report_type": "summarization", "status": "completed"},
                ],
                "total": 25,
            },
        )()

        with patch("services.orchestrator.presentation.api.reporting.routes.container") as mock_container:
            mock_container.list_reports_use_case.execute.return_value = mock_result

            response = client.get(
                "/api/v1/reporting/reports?report_type=pr_confidence&status=completed&page=1&page_size=10"
            )
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and listed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check reports listing events
            business_calls = mock_logger_client.log_business_event.call_args_list
            listing_started = next((call for call in business_calls if call[0][0] == "reports_listing_started"), None)
            reports_listed = next((call for call in business_calls if call[0][0] == "reports_listed"), None)

            assert listing_started is not None
            assert reports_listed is not None

            started_data = listing_started[0][1]
            assert started_data["filters_applied"] is True
            assert started_data["report_type_filter"] == "pr_confidence"
            assert started_data["status_filter"] == "completed"
            assert started_data["page"] == 1
            assert started_data["page_size"] == 10

            listed_data = reports_listed[0][1]
            assert listed_data["reports_returned"] == 2
            assert listed_data["filters_applied"] is True
            assert listed_data["total_available"] == 25

    @pytest.mark.asyncio
    async def test_report_templates_listing_logging_success(self, client, mock_logger_client):
        """Test report templates listing endpoint logging on success."""
        response = client.get("/api/v1/reporting/templates")
        assert response.status_code == 200

        # Verify logging calls
        assert mock_logger_client.log_business_event.call_count >= 2  # started and listed
        assert mock_logger_client.log_performance_metric.call_count == 1

        # Check report templates listing events
        business_calls = mock_logger_client.log_business_event.call_args_list
        templates_started = next(
            (call for call in business_calls if call[0][0] == "report_templates_listing_started"), None
        )
        templates_listed = next((call for call in business_calls if call[0][0] == "report_templates_listed"), None)

        assert templates_started is not None
        assert templates_listed is not None

        started_data = templates_started[0][1]
        assert started_data["operation"] == "report_template_management"
        assert started_data["template_repository_access"] is True

        listed_data = templates_listed[0][1]
        assert listed_data["templates_returned"] == 2  # pr-confidence and summarization
        assert listed_data["template_categories"] == 2
        assert listed_data["capability_inventory_complete"] is True

    @pytest.mark.asyncio
    async def test_report_template_detail_retrieval_logging_success(self, client, mock_logger_client):
        """Test report template detail retrieval endpoint logging on
        success."""
        template_id = "pr-confidence-template"

        response = client.get(f"/api/v1/reporting/templates/{template_id}")
        assert response.status_code == 200

        # Verify logging calls
        assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
        assert mock_logger_client.log_performance_metric.call_count == 1

        # Check template detail events
        business_calls = mock_logger_client.log_business_event.call_args_list
        detail_started = next((call for call in business_calls if call[0][0] == "report_template_detail_started"), None)
        detail_retrieved = next(
            (call for call in business_calls if call[0][0] == "report_template_detail_retrieved"), None
        )

        assert detail_started is not None
        assert detail_retrieved is not None

        started_data = detail_started[0][1]
        assert started_data["template_id"] == template_id
        assert started_data["query_type"] == "template_detail"
        assert started_data["data_scope"] == "individual_template"

        retrieved_data = detail_retrieved[0][1]
        assert retrieved_data["template_id"] == template_id
        assert retrieved_data["success"] is True
        assert retrieved_data["template_type"] == "pr_confidence"
        assert retrieved_data["parameter_count"] == 2  # repository and date_range
        assert retrieved_data["has_default_config"] is True

    @pytest.mark.asyncio
    async def test_report_template_detail_logging_not_found(self, client, mock_logger_client):
        """Test report template detail retrieval endpoint logging when template
        not found."""
        template_id = "nonexistent-template"

        response = client.get(f"/api/v1/reporting/templates/{template_id}")
        assert response.status_code == 404

        # Verify logging calls
        business_calls = mock_logger_client.log_business_event.call_args_list
        template_not_found = next((call for call in business_calls if call[0][0] == "report_template_not_found"), None)
        assert template_not_found is not None

        not_found_data = template_not_found[0][1]
        assert not_found_data["template_id"] == template_id
        assert not_found_data["template_status"] == "not_found"
        assert not_found_data["template_lookup_failed"] is True

    @pytest.mark.asyncio
    async def test_report_deletion_logging_placeholder(self, client, mock_logger_client):
        """Test report deletion endpoint logging (placeholder
        implementation)."""
        report_id = "report_12345"

        response = client.delete(f"/api/v1/reporting/reports/{report_id}")
        assert response.status_code == 501

        # Verify logging calls for placeholder
        assert mock_logger_client.log_business_event.call_count >= 2  # started and not_implemented

        # Check report deletion events
        business_calls = mock_logger_client.log_business_event.call_args_list
        deletion_started = next((call for call in business_calls if call[0][0] == "report_deletion_started"), None)
        not_implemented = next(
            (call for call in business_calls if call[0][0] == "report_deletion_not_implemented"), None
        )

        assert deletion_started is not None
        assert not_implemented is not None

        started_data = deletion_started[0][1]
        assert started_data["report_id"] == report_id
        assert started_data["control_type"] == "report_cleanup"
        assert started_data["storage_optimization"] is True

        not_impl_data = not_implemented[0][1]
        assert not_impl_data["report_id"] == report_id
        assert not_impl_data["implementation_status"] == "placeholder"
        assert not_impl_data["feature_planned"] is True

    @pytest.mark.asyncio
    async def test_report_types_listing_logging_success(self, client, mock_logger_client):
        """Test report types listing endpoint logging on success."""
        response = client.get("/api/v1/reporting/types")
        assert response.status_code == 200

        # Verify logging calls
        assert mock_logger_client.log_business_event.call_count >= 2  # started and listed
        assert mock_logger_client.log_performance_metric.call_count == 1

        # Check report types listing events
        business_calls = mock_logger_client.log_business_event.call_args_list
        types_started = next((call for call in business_calls if call[0][0] == "report_types_listing_started"), None)
        types_listed = next((call for call in business_calls if call[0][0] == "report_types_listed"), None)

        assert types_started is not None
        assert types_listed is not None

        started_data = types_started[0][1]
        assert started_data["operation"] == "report_capability_discovery"
        assert started_data["report_type_inventory"] is True

        listed_data = types_listed[0][1]
        assert listed_data["report_types_returned"] == 5  # pr_confidence, summarization, analytics, performance, health
        assert listed_data["total_parameters"] == 13  # Sum of all parameters across types
        assert listed_data["total_formats"] == 17  # Sum of all formats across types
        assert listed_data["capability_inventory_complete"] is True

    @pytest.mark.asyncio
    async def test_reporting_stats_retrieval_logging_success(self, client, mock_logger_client):
        """Test reporting stats retrieval endpoint logging on success."""
        response = client.get("/api/v1/reporting/stats")
        assert response.status_code == 200

        # Verify logging calls
        assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
        assert mock_logger_client.log_performance_metric.call_count == 1

        # Check reporting stats retrieval events
        business_calls = mock_logger_client.log_business_event.call_args_list
        stats_started = next(
            (call for call in business_calls if call[0][0] == "reporting_stats_retrieval_started"), None
        )
        stats_retrieved = next((call for call in business_calls if call[0][0] == "reporting_stats_retrieved"), None)

        assert stats_started is not None
        assert stats_retrieved is not None

        started_data = stats_started[0][1]
        assert started_data["operation"] == "reporting_system_monitoring"
        assert started_data["reporting_analytics"] is True

        retrieved_data = stats_retrieved[0][1]
        assert retrieved_data["success"] is True
        assert retrieved_data["stats_completeness"] == "placeholder_data"
        assert retrieved_data["metrics_available"] == 6  # total_reports, reports_generated_today, etc.
        assert retrieved_data["performance_data_included"] is True

    @pytest.mark.asyncio
    async def test_report_generation_logging_failure(self, client, mock_logger_client):
        """Test report generation endpoint logging on failure."""
        with patch("services.orchestrator.presentation.api.reporting.routes.container") as mock_container:
            mock_container.generate_report_use_case.execute.side_effect = ValueError("Invalid report parameters")

            report_request = {"report_type": "invalid_type", "parameters": {}, "format": "pdf"}
            response = client.post("/api/v1/reporting/generate", json=report_request)
            assert response.status_code == 500

            # Verify error logging
            assert mock_logger_client.log_error.call_count == 1
            assert mock_logger_client.log_business_event.call_count >= 2  # started and failed

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Report generation failed" in error_call[0][0]
            assert error_call[0][1]["report_type"] == "invalid_type"
            assert error_call[0][1]["error_type"] == "ValueError"

            # Check failure event
            business_calls = mock_logger_client.log_business_event.call_args_list
            generation_failed = next(
                (call for call in business_calls if call[0][0] == "report_generation_failed"), None
            )
            assert generation_failed is not None

    @pytest.mark.asyncio
    async def test_request_ids_generated_uniquely(self, client, mock_logger_client):
        """Test that all endpoints generate unique request IDs."""
        request_ids = set()

        with patch("services.orchestrator.presentation.api.reporting.routes.container") as mock_container:
            # Mock all the use cases to return success
            mock_result = {"report_id": "test", "reports": [{"report_id": "r1"}]}
            mock_container.generate_report_use_case.execute.return_value = mock_result
            mock_container.get_report_use_case.execute.return_value = mock_result
            mock_container.list_reports_use_case.execute.return_value = mock_result

            # Make requests to different endpoints
            client.post("/api/v1/reporting/generate", json={"report_type": "pr_confidence", "parameters": {}})
            client.get("/api/v1/reporting/reports/test-report")
            client.get("/api/v1/reporting/reports?page=1&page_size=10")
            client.get("/api/v1/reporting/templates")
            client.get("/api/v1/reporting/templates/test-template")
            client.delete("/api/v1/reporting/reports/test-report")
            client.get("/api/v1/reporting/types")
            client.get("/api/v1/reporting/stats")

            # Collect request IDs from business events
            business_calls = mock_logger_client.log_business_event.call_args_list
            for call in business_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get("request_id")
                    if request_id:
                        request_ids.add(request_id)

        # Should have collected multiple unique request IDs
        assert len(request_ids) >= 8  # At least one per endpoint

        # All request IDs should follow expected patterns
        for request_id in request_ids:
            assert any(
                prefix in request_id
                for prefix in [
                    "report_generation_",
                    "report_retrieval_",
                    "reports_listing_",
                    "templates_listing_",
                    "template_detail_",
                    "report_deletion_",
                    "report_types_",
                    "reporting_stats_",
                ]
            )

    @pytest.mark.asyncio
    async def test_performance_metrics_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        mock_result = {"report_id": "test"}

        with patch("services.orchestrator.presentation.api.reporting.routes.container") as mock_container:
            mock_container.get_report_use_case.execute.return_value = mock_result

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            response = client.get("/api/v1/reporting/reports/test-report")
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            retrieval_perf = next((call for call in perf_calls if call[0][0] == "report_retrieval"), None)
            assert retrieval_perf is not None

            processing_time = retrieval_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Patch get_logger_client to return None
        with patch("services.orchestrator.presentation.api.reporting.routes.get_logger_client") as mock_get_client:
            mock_get_client.return_value = None

            with patch("services.orchestrator.presentation.api.reporting.routes.container") as mock_container:
                mock_container.list_reports_use_case.execute.return_value = {"reports": []}

                # Make request - should still work without logging
                response = client.get("/api/v1/reporting/reports?page=1&page_size=10")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_business_events_comprehensive_coverage(self, client, mock_logger_client):
        """Test that all major business events are logged across reporting
        endpoints."""
        expected_events = {
            # Report generation events
            "report_generation_started",
            "report_generation_completed",
            "report_generation_failed",
            # Report retrieval events
            "report_retrieval_started",
            "report_retrieved",
            "report_not_found",
            "report_retrieval_failed",
            # Reports listing events
            "reports_listing_started",
            "reports_listed",
            "reports_listing_failed",
            # Report template events
            "report_templates_listing_started",
            "report_templates_listed",
            "report_templates_listing_failed",
            "report_template_detail_started",
            "report_template_detail_retrieved",
            "report_template_not_found",
            "report_template_detail_failed",
            # Report management events
            "report_deletion_started",
            "report_deletion_not_implemented",
            "report_deletion_failed",
            # Report capability events
            "report_types_listing_started",
            "report_types_listed",
            "report_types_listing_failed",
            # Reporting system monitoring events
            "reporting_stats_retrieval_started",
            "reporting_stats_retrieved",
            "reporting_stats_retrieval_failed",
        }

        # Test a representative sample of endpoints to verify event logging
        with patch("services.orchestrator.presentation.api.reporting.routes.container") as mock_container:
            # Mock successful responses
            mock_result = {"report_id": "test", "reports": [{"report_id": "r1"}]}
            mock_container.generate_report_use_case.execute.return_value = mock_result
            mock_container.get_report_use_case.execute.return_value = mock_result
            mock_container.list_reports_use_case.execute.return_value = mock_result

            # Make requests to key endpoints
            client.post("/api/v1/reporting/generate", json={"report_type": "pr_confidence", "parameters": {}})
            client.get("/api/v1/reporting/reports/test-report")
            client.get("/api/v1/reporting/reports?page=1&page_size=10")
            client.get("/api/v1/reporting/templates")
            client.get("/api/v1/reporting/templates/pr-confidence-template")
            client.delete("/api/v1/reporting/reports/test-report")
            client.get("/api/v1/reporting/types")
            client.get("/api/v1/reporting/stats")

            # Check which events were actually logged
            business_calls = mock_logger_client.log_business_event.call_args_list
            logged_events = {call[0][0] for call in business_calls}

            # Verify we logged some key events (not all, as some require specific conditions)
            key_events_logged = logged_events.intersection(
                {
                    "report_generation_started",
                    "report_generation_completed",
                    "report_retrieval_started",
                    "report_retrieved",
                    "reports_listing_started",
                    "reports_listed",
                    "report_templates_listing_started",
                    "report_templates_listed",
                    "report_template_detail_started",
                    "report_template_detail_retrieved",
                    "report_deletion_started",
                    "report_deletion_not_implemented",
                    "report_types_listing_started",
                    "report_types_listed",
                    "reporting_stats_retrieval_started",
                    "reporting_stats_retrieved",
                }
            )

            assert len(key_events_logged) >= 16  # Should have logged most key events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
