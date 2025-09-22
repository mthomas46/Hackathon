"""Tests for Orchestrator Query Processing Routes logging integration with LogCollectorClient."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestOrchestratorQueryProcessingLoggingIntegration:
    """Test Orchestrator Query Processing routes logging integration with LogCollectorClient."""

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
        # Patch the get_logger_client function in the query processing routes
        with patch(
            "services.orchestrator.presentation.api.query_processing.routes.get_logger_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_logger_client
            yield

    @pytest.mark.asyncio
    async def test_natural_language_query_processing_logging_success(self, client, mock_logger_client):
        """Test natural language query processing endpoint logging on success."""
        mock_result = {
            "results": [
                {"title": "AI Document", "score": 0.95, "content": "AI content..."},
                {"title": "ML Guide", "score": 0.87, "content": "ML content..."},
            ],
            "total_results": 2,
            "processing_time_ms": 250,
        }

        with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
            mock_container.process_natural_language_query_use_case.execute.return_value = mock_result

            query_request = {
                "query_text": "find documents about artificial intelligence",
                "context": {"domain": "technology"},
                "max_results": 10,
                "include_explanation": True,
            }
            response = client.post("/api/v1/query-processing/process", json=query_request)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and completed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check natural language query processing events
            business_calls = mock_logger_client.log_business_event.call_args_list
            query_started = next(
                (call for call in business_calls if call[0][0] == "natural_language_query_started"), None
            )
            query_completed = next(
                (call for call in business_calls if call[0][0] == "natural_language_query_completed"), None
            )

            assert query_started is not None
            assert query_completed is not None

            started_data = query_started[0][1]
            assert started_data["query_type"] == "natural_language"
            assert started_data["query_length"] == len(query_request["query_text"])
            assert started_data["max_results_requested"] == 10
            assert started_data["explanation_requested"] is True
            assert started_data["context_provided"] is True

            completed_data = query_completed[0][1]
            assert completed_data["success"] is True
            assert completed_data["results_returned"] == 2
            assert completed_data["max_results_requested"] == 10
            assert completed_data["explanation_included"] is True

    @pytest.mark.asyncio
    async def test_structured_query_execution_logging_success(self, client, mock_logger_client):
        """Test structured query execution endpoint logging on success."""
        mock_result = {
            "results": [
                {"id": "doc1", "title": "Document 1", "score": 0.92},
                {"id": "doc2", "title": "Document 2", "score": 0.88},
            ],
            "total_results": 2,
            "execution_time_ms": 180,
        }

        with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
            mock_container.process_natural_language_query_use_case.execute.return_value = mock_result

            structured_request = {
                "query_type": "semantic_search",
                "parameters": {"query": "machine learning", "threshold": 0.8},
                "filters": {"category": "technical", "date_range": "2024"},
                "sorting": {"field": "relevance", "order": "desc"},
                "pagination": {"page": 1, "page_size": 20},
            }
            response = client.post("/api/v1/query-processing/structured", json=structured_request)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and completed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check structured query execution events
            business_calls = mock_logger_client.log_business_event.call_args_list
            query_started = next((call for call in business_calls if call[0][0] == "structured_query_started"), None)
            query_completed = next(
                (call for call in business_calls if call[0][0] == "structured_query_completed"), None
            )

            assert query_started is not None
            assert query_completed is not None

            started_data = query_started[0][1]
            assert started_data["query_type"] == "semantic_search"
            assert started_data["parameters_count"] == 2
            assert started_data["filters_applied"] is True
            assert started_data["sorting_enabled"] is True
            assert started_data["pagination_used"] is True

            completed_data = query_completed[0][1]
            assert completed_data["query_type"] == "semantic_search"
            assert completed_data["results_returned"] == 2
            assert completed_data["filters_applied"] is True
            assert completed_data["sorting_used"] is True
            assert completed_data["pagination_applied"] is True

    @pytest.mark.asyncio
    async def test_query_result_retrieval_logging_success(self, client, mock_logger_client):
        """Test query result retrieval endpoint logging on success."""
        query_id = "query_12345"
        mock_result = {
            "query_id": query_id,
            "query_text": "find AI documents",
            "results": [
                {"id": "doc1", "title": "AI Guide", "content": "AI content..."},
                {"id": "doc2", "title": "ML Tutorial", "content": "ML content..."},
            ],
            "total_results": 2,
            "executed_at": "2024-01-01T10:00:00Z",
            "execution_time_ms": 150,
        }

        with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
            mock_container.get_query_result_use_case.execute.return_value = mock_result

            response = client.get(f"/api/v1/query-processing/results/{query_id}")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check query result retrieval events
            business_calls = mock_logger_client.log_business_event.call_args_list
            retrieval_started = next(
                (call for call in business_calls if call[0][0] == "query_result_retrieval_started"), None
            )
            result_retrieved = next((call for call in business_calls if call[0][0] == "query_result_retrieved"), None)

            assert retrieval_started is not None
            assert result_retrieved is not None

            started_data = retrieval_started[0][1]
            assert started_data["query_id"] == query_id
            assert started_data["data_scope"] == "stored_query_result"
            assert started_data["result_cache_access"] is True

            retrieved_data = result_retrieved[0][1]
            assert retrieved_data["query_id"] == query_id
            assert retrieved_data["success"] is True
            assert retrieved_data["cache_hit"] is True
            assert retrieved_data["result_format"] == "structured_response"

    @pytest.mark.asyncio
    async def test_query_result_retrieval_logging_not_found(self, client, mock_logger_client):
        """Test query result retrieval endpoint logging when result not found."""
        query_id = "nonexistent_query"

        with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
            mock_container.get_query_result_use_case.execute.return_value = None

            response = client.get(f"/api/v1/query-processing/results/{query_id}")
            assert response.status_code == 404

            # Verify logging calls
            business_calls = mock_logger_client.log_business_event.call_args_list
            result_not_found = next((call for call in business_calls if call[0][0] == "query_result_not_found"), None)
            assert result_not_found is not None

            not_found_data = result_not_found[0][1]
            assert not_found_data["query_id"] == query_id
            assert not_found_data["result_status"] == "not_found"
            assert not_found_data["cache_miss"] is True

    @pytest.mark.asyncio
    async def test_query_history_listing_logging_with_filters(self, client, mock_logger_client):
        """Test query history listing endpoint logging with various filters."""
        mock_result = type(
            "MockResult",
            (),
            {
                "queries": [
                    {"query_id": "q1", "intent": "search", "status": "completed"},
                    {"query_id": "q2", "intent": "analytics", "status": "completed"},
                ],
                "total": 15,
            },
        )()

        with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
            mock_container.list_queries_use_case.execute.return_value = mock_result

            response = client.get("/api/v1/query-processing/history?intent=search&status=completed&page=1&page_size=10")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and listed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check query history listing events
            business_calls = mock_logger_client.log_business_event.call_args_list
            listing_started = next(
                (call for call in business_calls if call[0][0] == "query_history_listing_started"), None
            )
            history_listed = next((call for call in business_calls if call[0][0] == "query_history_listed"), None)

            assert listing_started is not None
            assert history_listed is not None

            started_data = listing_started[0][1]
            assert started_data["filters_applied"] is True
            assert started_data["intent_filter"] == "search"
            assert started_data["status_filter"] == "completed"
            assert started_data["page"] == 1
            assert started_data["page_size"] == 10

            listed_data = history_listed[0][1]
            assert listed_data["queries_returned"] == 2
            assert listed_data["filters_applied"] is True
            assert listed_data["total_available"] == 15

    @pytest.mark.asyncio
    async def test_query_history_detail_retrieval_logging_success(self, client, mock_logger_client):
        """Test query history detail retrieval endpoint logging on success."""
        query_id = "query_12345"
        mock_result = {
            "query_id": query_id,
            "query_text": "analyze code quality",
            "execution_events": [
                {"event": "started", "timestamp": "2024-01-01T10:00:00Z"},
                {"event": "processing", "timestamp": "2024-01-01T10:00:05Z"},
                {"event": "completed", "timestamp": "2024-01-01T10:00:15Z"},
            ],
            "performance_metrics": {"execution_time_ms": 15000, "cpu_usage": 0.75, "memory_usage": 0.60},
            "result_summary": {"total_results": 25, "success_rate": 0.92},
        }

        with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
            mock_container.list_queries_use_case.execute.return_value = mock_result

            response = client.get(f"/api/v1/query-processing/history/{query_id}")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check query history detail events
            business_calls = mock_logger_client.log_business_event.call_args_list
            detail_started = next(
                (call for call in business_calls if call[0][0] == "query_history_detail_started"), None
            )
            detail_retrieved = next(
                (call for call in business_calls if call[0][0] == "query_history_detail_retrieved"), None
            )

            assert detail_started is not None
            assert detail_retrieved is not None

            started_data = detail_started[0][1]
            assert started_data["query_id"] == query_id
            assert started_data["history_type"] == "individual_query_timeline"
            assert started_data["includes_performance_metrics"] is True

            retrieved_data = detail_retrieved[0][1]
            assert retrieved_data["query_id"] == query_id
            assert retrieved_data["success"] is True
            assert retrieved_data["history_completeness"] == "full_lifecycle"
            assert retrieved_data["execution_events_count"] == 3
            assert retrieved_data["performance_data_included"] is True

    @pytest.mark.asyncio
    async def test_query_intents_listing_logging_success(self, client, mock_logger_client):
        """Test query intents listing endpoint logging on success."""
        response = client.get("/api/v1/query-processing/intents")
        assert response.status_code == 200

        # Verify logging calls
        assert mock_logger_client.log_business_event.call_count >= 2  # started and listed
        assert mock_logger_client.log_performance_metric.call_count == 1

        # Check query intents listing events
        business_calls = mock_logger_client.log_business_event.call_args_list
        intents_started = next((call for call in business_calls if call[0][0] == "query_intents_listing_started"), None)
        intents_listed = next((call for call in business_calls if call[0][0] == "query_intents_listed"), None)

        assert intents_started is not None
        assert intents_listed is not None

        started_data = intents_started[0][1]
        assert started_data["operation"] == "query_capability_discovery"
        assert started_data["intent_inventory"] is True

        listed_data = intents_listed[0][1]
        assert listed_data["intents_returned"] == 5  # search, analytics, summarize, explain, compare
        assert listed_data["intent_categories"] == 5
        assert listed_data["capability_inventory_complete"] is True

    @pytest.mark.asyncio
    async def test_query_result_deletion_logging_placeholder(self, client, mock_logger_client):
        """Test query result deletion endpoint logging (placeholder implementation)."""
        query_id = "query_12345"

        response = client.delete(f"/api/v1/query-processing/results/{query_id}")
        assert response.status_code == 501

        # Verify logging calls for placeholder
        assert mock_logger_client.log_business_event.call_count >= 2  # started and not_implemented

        # Check query result deletion events
        business_calls = mock_logger_client.log_business_event.call_args_list
        deletion_started = next(
            (call for call in business_calls if call[0][0] == "query_result_deletion_started"), None
        )
        not_implemented = next(
            (call for call in business_calls if call[0][0] == "query_result_deletion_not_implemented"), None
        )

        assert deletion_started is not None
        assert not_implemented is not None

        started_data = deletion_started[0][1]
        assert started_data["query_id"] == query_id
        assert started_data["control_type"] == "result_cleanup"
        assert started_data["privacy_compliance"] is True

        not_impl_data = not_implemented[0][1]
        assert not_impl_data["query_id"] == query_id
        assert not_impl_data["implementation_status"] == "placeholder"
        assert not_impl_data["feature_planned"] is True

    @pytest.mark.asyncio
    async def test_query_stats_retrieval_logging_success(self, client, mock_logger_client):
        """Test query stats retrieval endpoint logging on success."""
        response = client.get("/api/v1/query-processing/stats")
        assert response.status_code == 200

        # Verify logging calls
        assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
        assert mock_logger_client.log_performance_metric.call_count == 1

        # Check query stats retrieval events
        business_calls = mock_logger_client.log_business_event.call_args_list
        stats_started = next((call for call in business_calls if call[0][0] == "query_stats_retrieval_started"), None)
        stats_retrieved = next((call for call in business_calls if call[0][0] == "query_stats_retrieved"), None)

        assert stats_started is not None
        assert stats_retrieved is not None

        started_data = stats_started[0][1]
        assert started_data["operation"] == "query_system_monitoring"
        assert started_data["performance_analytics"] is True

        retrieved_data = stats_retrieved[0][1]
        assert retrieved_data["success"] is True
        assert retrieved_data["stats_completeness"] == "placeholder_data"
        assert retrieved_data["metrics_available"] == 6  # total_queries, queries_today, etc.
        assert retrieved_data["performance_data_included"] is True

    @pytest.mark.asyncio
    async def test_natural_language_query_processing_logging_failure(self, client, mock_logger_client):
        """Test natural language query processing endpoint logging on failure."""
        with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
            mock_container.process_natural_language_query_use_case.execute.side_effect = ValueError(
                "Query parsing failed"
            )

            query_request = {"query_text": "invalid query syntax {{{", "max_results": 5}
            response = client.post("/api/v1/query-processing/process", json=query_request)
            assert response.status_code == 500

            # Verify error logging
            assert mock_logger_client.log_error.call_count == 1
            assert mock_logger_client.log_business_event.call_count >= 2  # started and failed

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Natural language query processing failed" in error_call[0][0]
            assert error_call[0][1]["query_length"] == len(query_request["query_text"])
            assert error_call[0][1]["error_type"] == "ValueError"

            # Check failure event
            business_calls = mock_logger_client.log_business_event.call_args_list
            query_failed = next(
                (call for call in business_calls if call[0][0] == "natural_language_query_failed"), None
            )
            assert query_failed is not None

    @pytest.mark.asyncio
    async def test_request_ids_generated_uniquely(self, client, mock_logger_client):
        """Test that all endpoints generate unique request IDs."""
        request_ids = set()

        with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
            # Mock all the use cases to return success
            mock_result = {"query_id": "test", "results": [{"id": "result1"}], "queries": [{"query_id": "q1"}]}
            mock_container.process_natural_language_query_use_case.execute.return_value = mock_result
            mock_container.get_query_result_use_case.execute.return_value = mock_result
            mock_container.list_queries_use_case.execute.return_value = mock_result

            # Make requests to different endpoints
            client.post("/api/v1/query-processing/process", json={"query_text": "test query", "max_results": 5})
            client.post("/api/v1/query-processing/structured", json={"query_type": "search", "parameters": {}})
            client.get("/api/v1/query-processing/results/test-query")
            client.get("/api/v1/query-processing/history?page=1&page_size=10")
            client.get("/api/v1/query-processing/history/test-query")
            client.get("/api/v1/query-processing/intents")
            client.delete("/api/v1/query-processing/results/test-query")
            client.get("/api/v1/query-processing/stats")

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
                    "nl_query_",
                    "structured_query_",
                    "query_result_",
                    "query_history_",
                    "query_history_detail_",
                    "query_intents_",
                    "query_result_delete_",
                    "query_stats_",
                ]
            )

    @pytest.mark.asyncio
    async def test_performance_metrics_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        mock_result = {"results": [{"id": "result1"}], "query_id": "test"}

        with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
            mock_container.get_query_result_use_case.execute.return_value = mock_result

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            response = client.get("/api/v1/query-processing/results/test-query")
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            result_perf = next((call for call in perf_calls if call[0][0] == "query_result_retrieval"), None)
            assert result_perf is not None

            processing_time = result_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Patch get_logger_client to return None
        with patch(
            "services.orchestrator.presentation.api.query_processing.routes.get_logger_client"
        ) as mock_get_client:
            mock_get_client.return_value = None

            with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
                mock_container.list_queries_use_case.execute.return_value = {"queries": []}

                # Make request - should still work without logging
                response = client.get("/api/v1/query-processing/history?page=1&page_size=10")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_business_events_comprehensive_coverage(self, client, mock_logger_client):
        """Test that all major business events are logged across query processing endpoints."""
        expected_events = {
            # Natural language query events
            "natural_language_query_started",
            "natural_language_query_completed",
            "natural_language_query_failed",
            # Structured query events
            "structured_query_started",
            "structured_query_completed",
            "structured_query_failed",
            # Query result events
            "query_result_retrieval_started",
            "query_result_retrieved",
            "query_result_not_found",
            "query_result_retrieval_failed",
            # Query history events
            "query_history_listing_started",
            "query_history_listed",
            "query_history_listing_failed",
            "query_history_detail_started",
            "query_history_detail_retrieved",
            "query_history_not_found",
            "query_history_detail_failed",
            # Query intents events
            "query_intents_listing_started",
            "query_intents_listed",
            "query_intents_listing_failed",
            # Query result management events
            "query_result_deletion_started",
            "query_result_deletion_not_implemented",
            "query_result_deletion_failed",
            # Query system monitoring events
            "query_stats_retrieval_started",
            "query_stats_retrieved",
            "query_stats_retrieval_failed",
        }

        # Test a representative sample of endpoints to verify event logging
        with patch("services.orchestrator.presentation.api.query_processing.routes.container") as mock_container:
            # Mock successful responses
            mock_result = {"query_id": "test", "results": [{"id": "result1"}], "queries": [{"query_id": "q1"}]}
            mock_container.process_natural_language_query_use_case.execute.return_value = mock_result
            mock_container.get_query_result_use_case.execute.return_value = mock_result
            mock_container.list_queries_use_case.execute.return_value = mock_result

            # Make requests to key endpoints
            client.post("/api/v1/query-processing/process", json={"query_text": "test query", "max_results": 5})
            client.post("/api/v1/query-processing/structured", json={"query_type": "search", "parameters": {}})
            client.get("/api/v1/query-processing/results/test-query")
            client.get("/api/v1/query-processing/history?page=1&page_size=10")
            client.get("/api/v1/query-processing/history/test-query")
            client.get("/api/v1/query-processing/intents")
            client.delete("/api/v1/query-processing/results/test-query")
            client.get("/api/v1/query-processing/stats")

            # Check which events were actually logged
            business_calls = mock_logger_client.log_business_event.call_args_list
            logged_events = {call[0][0] for call in business_calls}

            # Verify we logged some key events (not all, as some require specific conditions)
            key_events_logged = logged_events.intersection(
                {
                    "natural_language_query_started",
                    "natural_language_query_completed",
                    "structured_query_started",
                    "structured_query_completed",
                    "query_result_retrieval_started",
                    "query_result_retrieved",
                    "query_history_listing_started",
                    "query_history_listed",
                    "query_history_detail_started",
                    "query_history_detail_retrieved",
                    "query_intents_listing_started",
                    "query_intents_listed",
                    "query_result_deletion_started",
                    "query_result_deletion_not_implemented",
                    "query_stats_retrieval_started",
                    "query_stats_retrieved",
                }
            )

            assert len(key_events_logged) >= 16  # Should have logged most key events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
