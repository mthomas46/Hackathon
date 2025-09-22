"""Tests for Doc Store Additional Handlers logging integration with LogCollectorClient."""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.shared.utilities.logging_client import LogCollectorClient


class TestDocStoreHandlersLoggingIntegration:
    """Test Doc Store additional handlers logging integration with LogCollectorClient."""

    @pytest.fixture
    def mock_logger_client(self):
        """Mock LogCollectorClient."""
        mock_client = AsyncMock(spec=LogCollectorClient)
        return mock_client

    @pytest.fixture(autouse=True)
    async def setup_logger_client(self, mock_logger_client):
        """Setup mock logger client for all tests."""
        # Patch the get_logger_client function in both analytics and bulk handlers
        with patch(
            "services.doc_store.domain.analytics.handlers.get_logger_client"
        ) as mock_analytics_get_client, patch(
            "services.doc_store.domain.bulk.handlers.get_logger_client"
        ) as mock_bulk_get_client:

            mock_analytics_get_client.return_value = mock_logger_client
            mock_bulk_get_client.return_value = mock_logger_client
            yield

    @pytest.mark.asyncio
    async def test_document_analytics_retrieval_logging_success(self, mock_logger_client):
        """Test document analytics retrieval endpoint logging on success."""
        mock_analytics = type(
            "MockAnalytics",
            (),
            {
                "total_documents": 150,
                "total_analyses": 75,
                "total_ensembles": 25,
                "total_style_examples": 10,
                "storage_stats": {"total_size_mb": 500, "avg_doc_size_kb": 3.2},
                "temporal_trends": {"daily_growth": 5.2},
                "content_insights": {"avg_quality_score": 8.5},
                "relationship_insights": {"connection_density": 0.15},
            },
        )()

        with patch("services.doc_store.domain.analytics.handlers.AnalyticsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.generate_analytics.return_value = mock_analytics
            mock_service.get_quality_metrics.return_value = {"avg_score": 8.5, "distribution": [5, 15, 30, 35, 15]}
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.doc_store.domain.analytics.handlers import AnalyticsHandlers

            handler = AnalyticsHandlers()

            result = await handler.handle_get_analytics(days_back=30)

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check analytics retrieval events
            business_calls = mock_logger_client.log_business_event.call_args_list
            retrieval_started = next(
                (call for call in business_calls if call[0][0] == "document_analytics_retrieval_started"), None
            )
            analytics_retrieved = next(
                (call for call in business_calls if call[0][0] == "document_analytics_retrieved"), None
            )

            assert retrieval_started is not None
            assert analytics_retrieved is not None

            started_data = retrieval_started[0][1]
            assert started_data["time_range_days"] == 30
            assert started_data["analytics_scope"] == "comprehensive_dashboard"
            assert started_data["data_aggregation_required"] is True
            assert started_data["performance_insights_requested"] is True

            retrieved_data = analytics_retrieved[0][1]
            assert retrieved_data["time_range_days"] == 30
            assert retrieved_data["success"] is True
            assert retrieved_data["total_documents_analyzed"] == 150
            assert retrieved_data["total_analyses_processed"] == 75
            assert retrieved_data["analytics_data_generated"] is True

    @pytest.mark.asyncio
    async def test_bulk_document_creation_logging_success(self, mock_logger_client):
        """Test bulk document creation endpoint logging on success."""
        mock_operation = type(
            "MockOperation",
            (),
            {
                "id": "bulk_op_12345",
                "operation_type": "create_documents",
                "to_dict": lambda: {"id": "bulk_op_12345", "status": "pending", "items_count": 10},
            },
        )()

        documents = [
            {"id": "doc1", "content": "Document 1 content", "metadata": {"author": "user1"}},
            {"id": "doc2", "content": "Document 2 content", "metadata": {"author": "user2"}},
        ]

        with patch("services.doc_store.domain.bulk.handlers.BulkOperationsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_bulk_operation.return_value = mock_operation
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.doc_store.domain.bulk.handlers import BulkOperationsHandlers

            handler = BulkOperationsHandlers()

            result = await handler.handle_bulk_create_documents(documents)

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and created
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check bulk creation events
            business_calls = mock_logger_client.log_business_event.call_args_list
            creation_started = next(
                (call for call in business_calls if call[0][0] == "bulk_documents_creation_started"), None
            )
            documents_created = next((call for call in business_calls if call[0][0] == "bulk_documents_created"), None)

            assert creation_started is not None
            assert documents_created is not None

            started_data = creation_started[0][1]
            assert started_data["documents_count"] == 2
            assert started_data["operation_type"] == "bulk_create_documents"
            assert started_data["batch_processing_required"] is True
            assert started_data["transaction_scope"] == "bulk_operation"

            created_data = documents_created[0][1]
            assert created_data["operation_id"] == "bulk_op_12345"
            assert created_data["success"] is True
            assert created_data["documents_count"] == 2
            assert created_data["bulk_operation_type"] == "create_documents"
            assert created_data["batch_processing_completed"] is True

    @pytest.mark.asyncio
    async def test_bulk_document_creation_logging_empty_request(self, mock_logger_client):
        """Test bulk document creation endpoint logging on empty request."""
        with patch("services.doc_store.domain.bulk.handlers.BulkOperationsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.doc_store.domain.bulk.handlers import BulkOperationsHandlers

            handler = BulkOperationsHandlers()

            result = await handler.handle_bulk_create_documents([])

            # Verify logging calls for empty request
            business_calls = mock_logger_client.log_business_event.call_args_list
            creation_rejected = next(
                (call for call in business_calls if call[0][0] == "bulk_documents_creation_rejected"), None
            )
            assert creation_rejected is not None

            rejected_data = creation_rejected[0][1]
            assert rejected_data["operation_type"] == "bulk_create_documents"
            assert rejected_data["error_type"] == "empty_request"
            assert rejected_data["documents_count"] == 0
            assert rejected_data["validation_failed"] is True

    @pytest.mark.asyncio
    async def test_document_analytics_retrieval_logging_failure(self, mock_logger_client):
        """Test document analytics retrieval endpoint logging on failure."""
        with patch("services.doc_store.domain.analytics.handlers.AnalyticsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.generate_analytics.side_effect = Exception("Analytics computation failed")
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.doc_store.domain.analytics.handlers import AnalyticsHandlers

            handler = AnalyticsHandlers()

            result = await handler.handle_get_analytics(days_back=7)

            # Verify error logging
            assert mock_logger_client.log_error.call_count == 1
            business_calls = mock_logger_client.log_business_event.call_args_list
            retrieval_failed = next(
                (call for call in business_calls if call[0][0] == "document_analytics_retrieval_failed"), None
            )
            assert retrieval_failed is not None

            failed_data = retrieval_failed[0][1]
            assert failed_data["time_range_days"] == 7
            assert failed_data["error_type"] == "Exception"
            assert "Analytics computation failed" in failed_data["error_message"]

    @pytest.mark.asyncio
    async def test_bulk_document_creation_logging_failure(self, mock_logger_client):
        """Test bulk document creation endpoint logging on failure."""
        documents = [{"id": "doc1", "content": "Document content"}]

        with patch("services.doc_store.domain.bulk.handlers.BulkOperationsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_bulk_operation.side_effect = Exception("Bulk operation failed")
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.doc_store.domain.bulk.handlers import BulkOperationsHandlers

            handler = BulkOperationsHandlers()

            result = await handler.handle_bulk_document_creation(documents)

            # Verify error logging
            assert mock_logger_client.log_error.call_count == 1
            business_calls = mock_logger_client.log_business_event.call_args_list
            creation_failed = next(
                (call for call in business_calls if call[0][0] == "bulk_documents_creation_failed"), None
            )
            assert creation_failed is not None

            failed_data = creation_failed[0][1]
            assert failed_data["operation_type"] == "bulk_create_documents"
            assert failed_data["error_type"] == "Exception"
            assert "Bulk operation failed" in failed_data["error_message"]

    @pytest.mark.asyncio
    async def test_request_ids_generated_uniquely(self, mock_logger_client):
        """Test that all doc store handlers generate unique request IDs."""
        request_ids = set()

        # Mock services
        mock_analytics = type(
            "MockAnalytics",
            (),
            {
                "total_documents": 100,
                "total_analyses": 50,
                "total_ensembles": 20,
                "total_style_examples": 5,
                "storage_stats": {"total_size_mb": 250},
                "temporal_trends": {},
                "content_insights": {},
                "relationship_insights": {},
            },
        )()

        mock_operation = type("MockOperation", (), {"id": "bulk_op_test", "to_dict": lambda: {"id": "bulk_op_test"}})()

        with patch(
            "services.doc_store.domain.analytics.handlers.AnalyticsService"
        ) as mock_analytics_service_class, patch(
            "services.doc_store.domain.bulk.handlers.BulkOperationsService"
        ) as mock_bulk_service_class:

            mock_analytics_service = MagicMock()
            mock_analytics_service.generate_analytics.return_value = mock_analytics
            mock_analytics_service.get_quality_metrics.return_value = {"avg_score": 8.0}
            mock_analytics_service_class.return_value = mock_analytics_service

            mock_bulk_service = MagicMock()
            mock_bulk_service.create_bulk_operation.return_value = mock_operation
            mock_bulk_service_class.return_value = mock_bulk_service

            # Test analytics handler
            from services.doc_store.domain.analytics.handlers import AnalyticsHandlers

            analytics_handler = AnalyticsHandlers()
            await analytics_handler.handle_get_analytics(days_back=30)

            # Test bulk operations handler
            from services.doc_store.domain.bulk.handlers import BulkOperationsHandlers

            bulk_handler = BulkOperationsHandlers()
            await bulk_handler.handle_bulk_create_documents([{"id": "doc1", "content": "Test content"}])

            # Collect request IDs from business events
            business_calls = mock_logger_client.log_business_event.call_args_list
            for call in business_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get("request_id")
                    if request_id:
                        request_ids.add(request_id)

        # Should have collected multiple unique request IDs
        assert len(request_ids) >= 2  # At least one per handler

        # All request IDs should follow expected patterns
        for request_id in request_ids:
            assert any(prefix in request_id for prefix in ["doc_analytics_comprehensive_", "bulk_doc_create_"])

    @pytest.mark.asyncio
    async def test_performance_metrics_accuracy(self, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        mock_analytics = type(
            "MockAnalytics",
            (),
            {
                "total_documents": 200,
                "total_analyses": 100,
                "total_ensembles": 30,
                "total_style_examples": 15,
                "storage_stats": {"total_size_mb": 750},
                "temporal_trends": {"growth_rate": 8.5},
                "content_insights": {"quality_avg": 9.2},
                "relationship_insights": {"density": 0.22},
            },
        )()

        with patch("services.doc_store.domain.analytics.handlers.AnalyticsService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.generate_analytics.return_value = mock_analytics
            mock_service.get_quality_metrics.return_value = {"avg_score": 9.2}
            mock_service_class.return_value = mock_service

            # Import and instantiate the handler
            from services.doc_store.domain.analytics.handlers import AnalyticsHandlers

            handler = AnalyticsHandlers()

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            result = await handler.handle_get_analytics(days_back=30)

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            analytics_perf = next((call for call in perf_calls if call[0][0] == "document_analytics_computation"), None)
            assert analytics_perf is not None

            processing_time = analytics_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self):
        """Test graceful handling when logging is disabled."""
        # Patch get_logger_client to return None
        with patch(
            "services.doc_store.domain.analytics.handlers.get_logger_client"
        ) as mock_analytics_get_client, patch(
            "services.doc_store.domain.bulk.handlers.get_logger_client"
        ) as mock_bulk_get_client:

            mock_analytics_get_client.return_value = None
            mock_bulk_get_client.return_value = None

            mock_analytics = type(
                "MockAnalytics",
                (),
                {
                    "total_documents": 50,
                    "total_analyses": 25,
                    "total_ensembles": 10,
                    "total_style_examples": 3,
                    "storage_stats": {"total_size_mb": 150},
                    "temporal_trends": {},
                    "content_insights": {},
                    "relationship_insights": {},
                },
            )()

            mock_operation = type(
                "MockOperation", (), {"id": "bulk_op_test", "to_dict": lambda: {"id": "bulk_op_test"}}
            )()

            with patch(
                "services.doc_store.domain.analytics.handlers.AnalyticsService"
            ) as mock_analytics_service_class, patch(
                "services.doc_store.domain.bulk.handlers.BulkOperationsService"
            ) as mock_bulk_service_class:

                mock_analytics_service = MagicMock()
                mock_analytics_service.generate_analytics.return_value = mock_analytics
                mock_analytics_service.get_quality_metrics.return_value = {"avg_score": 7.5}
                mock_analytics_service_class.return_value = mock_analytics_service

                mock_bulk_service = MagicMock()
                mock_bulk_service.create_bulk_operation.return_value = mock_operation
                mock_bulk_service_class.return_value = mock_bulk_service

                # Test analytics handler
                from services.doc_store.domain.analytics.handlers import AnalyticsHandlers

                analytics_handler = AnalyticsHandlers()
                result = await analytics_handler.handle_get_analytics(days_back=14)
                assert result["status"] == "success"  # Should still work without logging

                # Test bulk operations handler
                from services.doc_store.domain.bulk.handlers import BulkOperationsHandlers

                bulk_handler = BulkOperationsHandlers()
                result = await bulk_handler.handle_bulk_create_documents([{"id": "doc1", "content": "Test content"}])
                assert result["status"] == "success"  # Should still work without logging

    @pytest.mark.asyncio
    async def test_business_events_comprehensive_coverage(self, mock_logger_client):
        """Test that all major business events are logged across doc store handlers."""
        expected_events = {
            # Document analytics events
            "document_analytics_retrieval_started",
            "document_analytics_retrieved",
            "document_analytics_retrieval_failed",
            # Bulk operations events
            "bulk_documents_creation_started",
            "bulk_documents_created",
            "bulk_documents_creation_rejected",
            "bulk_documents_creation_failed",
        }

        # Test representative methods from each handler
        mock_analytics = type(
            "MockAnalytics",
            (),
            {
                "total_documents": 75,
                "total_analyses": 35,
                "total_ensembles": 15,
                "total_style_examples": 8,
                "storage_stats": {"total_size_mb": 300},
                "temporal_trends": {"trend": "increasing"},
                "content_insights": {"insight": "good"},
                "relationship_insights": {"density": 0.12},
            },
        )()

        mock_operation = type("MockOperation", (), {"id": "bulk_op_test", "to_dict": lambda: {"id": "bulk_op_test"}})()

        with patch(
            "services.doc_store.domain.analytics.handlers.AnalyticsService"
        ) as mock_analytics_service_class, patch(
            "services.doc_store.domain.bulk.handlers.BulkOperationsService"
        ) as mock_bulk_service_class:

            mock_analytics_service = MagicMock()
            mock_analytics_service.generate_analytics.return_value = mock_analytics
            mock_analytics_service.get_quality_metrics.return_value = {"avg_score": 8.3}
            mock_analytics_service_class.return_value = mock_analytics_service

            mock_bulk_service = MagicMock()
            mock_bulk_service.create_bulk_operation.return_value = mock_operation
            mock_bulk_service_class.return_value = mock_bulk_service

            # Test analytics handler methods
            from services.doc_store.domain.analytics.handlers import AnalyticsHandlers

            analytics_handler = AnalyticsHandlers()
            await analytics_handler.handle_get_analytics(days_back=30)

            # Test bulk operations handler methods
            from services.doc_store.domain.bulk.handlers import BulkOperationsHandlers

            bulk_handler = BulkOperationsHandlers()
            await bulk_handler.handle_bulk_create_documents(
                [{"id": "doc1", "content": "Content 1"}, {"id": "doc2", "content": "Content 2"}]
            )

            # Check which events were actually logged
            business_calls = mock_logger_client.log_business_event.call_args_list
            logged_events = {call[0][0] for call in business_calls}

            # Verify we logged key events (not all, as some require specific error conditions)
            key_events_logged = logged_events.intersection(
                {
                    "document_analytics_retrieval_started",
                    "document_analytics_retrieved",
                    "bulk_documents_creation_started",
                    "bulk_documents_created",
                }
            )

            assert len(key_events_logged) >= 4  # Should have logged most key events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
