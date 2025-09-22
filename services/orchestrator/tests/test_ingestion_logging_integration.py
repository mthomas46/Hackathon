"""Tests for Orchestrator Ingestion Routes logging integration with LogCollectorClient."""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

from services.shared.utilities.logging_client import LogCollectorClient


class TestOrchestratorIngestionLoggingIntegration:
    """Test Orchestrator Ingestion routes logging integration with LogCollectorClient."""

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
        # Patch the get_logger_client function in the ingestion routes
        with patch("services.orchestrator.presentation.api.ingestion.routes.get_logger_client") as mock_get_client:
            mock_get_client.return_value = mock_logger_client
            yield

    @pytest.mark.asyncio
    async def test_ingestion_workflow_creation_logging_success(self, client, mock_logger_client):
        """Test ingestion workflow creation endpoint logging on success."""
        mock_result = {"ingestion_id": "ingestion-123", "status": "started", "message": "Ingestion workflow initiated"}

        with patch("services.orchestrator.presentation.api.ingestion.routes.container") as mock_container:
            mock_container.start_ingestion_use_case.execute.return_value = mock_result

            ingestion_request = {
                "source_url": "https://github.com/user/repo",
                "source_type": "github",
                "parameters": {"branch": "main", "depth": 1},
            }
            response = client.post("/api/v1/ingestion/ingest", json=ingestion_request)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and created
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check ingestion workflow creation events
            business_calls = mock_logger_client.log_business_event.call_args_list
            workflow_started = next(
                (call for call in business_calls if call[0][0] == "ingestion_workflow_started"), None
            )
            workflow_created = next(
                (call for call in business_calls if call[0][0] == "ingestion_workflow_created"), None
            )

            assert workflow_started is not None
            assert workflow_created is not None

            started_data = workflow_started[0][1]
            assert started_data["source_url"] == "https://github.com/user/repo"
            assert started_data["source_type"] == "github"
            assert started_data["parameters_count"] == 2
            assert started_data["workflow_initiation"] is True

            created_data = workflow_created[0][1]
            assert created_data["ingestion_id"] == "ingestion-123"
            assert created_data["source_url"] == "https://github.com/user/repo"
            assert created_data["source_type"] == "github"
            assert created_data["workflow_status"] == "initialized"

    @pytest.mark.asyncio
    async def test_ingestion_status_retrieval_logging_success(self, client, mock_logger_client):
        """Test ingestion status retrieval endpoint logging on success."""
        mock_result = {
            "ingestion_id": "ingestion-123",
            "status": "processing",
            "progress": 65,
            "processed_count": 13,
            "total_count": 20,
            "started_at": "2024-01-01T10:00:00Z",
            "source_url": "https://github.com/user/repo",
        }

        with patch("services.orchestrator.presentation.api.ingestion.routes.container") as mock_container:
            mock_container.get_ingestion_status_use_case.execute.return_value = mock_result

            response = client.get("/api/v1/ingestion/ingest/ingestion-123")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check ingestion status retrieved event
            business_calls = mock_logger_client.log_business_event.call_args_list
            status_retrieved = next(
                (call for call in business_calls if call[0][0] == "ingestion_status_retrieved"), None
            )
            assert status_retrieved is not None

            retrieved_data = status_retrieved[0][1]
            assert retrieved_data["ingestion_id"] == "ingestion-123"
            assert retrieved_data["workflow_status"] == "processing"
            assert retrieved_data["progress_percentage"] == 65
            assert retrieved_data["documents_processed"] == 13
            assert retrieved_data["total_documents"] == 20

    @pytest.mark.asyncio
    async def test_ingestion_status_retrieval_logging_not_found(self, client, mock_logger_client):
        """Test ingestion status retrieval endpoint logging when ingestion not found."""
        with patch("services.orchestrator.presentation.api.ingestion.routes.container") as mock_container:
            mock_container.get_ingestion_status_use_case.execute.return_value = None

            response = client.get("/api/v1/ingestion/ingest/nonexistent-ingestion")
            assert response.status_code == 404

            # Verify logging calls
            business_calls = mock_logger_client.log_business_event.call_args_list
            ingestion_not_found = next((call for call in business_calls if call[0][0] == "ingestion_not_found"), None)
            assert ingestion_not_found is not None

            not_found_data = ingestion_not_found[0][1]
            assert not_found_data["ingestion_id"] == "nonexistent-ingestion"
            assert not_found_data["query_result"] == "not_found"

    @pytest.mark.asyncio
    async def test_ingestion_listing_logging_with_filters(self, client, mock_logger_client):
        """Test ingestion listing endpoint logging with various filters."""
        mock_result = type(
            "MockResult",
            (),
            {
                "ingestions": [
                    {"ingestion_id": "ing-1", "status": "completed", "source_type": "github"},
                    {"ingestion_id": "ing-2", "status": "processing", "source_type": "jira"},
                ],
                "total": 15,
            },
        )()

        with patch("services.orchestrator.presentation.api.ingestion.routes.container") as mock_container:
            mock_container.list_ingestions_use_case.execute.return_value = mock_result

            response = client.get("/api/v1/ingestion/ingest?status=completed&source_type=github&limit=10")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and completed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check ingestion listing events
            business_calls = mock_logger_client.log_business_event.call_args_list
            listing_started = next((call for call in business_calls if call[0][0] == "ingestion_listing_started"), None)
            listing_completed = next(
                (call for call in business_calls if call[0][0] == "ingestion_listing_completed"), None
            )

            assert listing_started is not None
            assert listing_completed is not None

            started_data = listing_started[0][1]
            assert started_data["filters_applied"] is True
            assert started_data["status_filter"] == "completed"
            assert started_data["source_type_filter"] == "github"
            assert started_data["limit"] == 10

            completed_data = listing_completed[0][1]
            assert completed_data["ingestions_returned"] == 2
            assert completed_data["filters_applied"] is True
            assert completed_data["total_available"] == 15

    @pytest.mark.asyncio
    async def test_document_metadata_retrieval_logging_placeholder(self, client, mock_logger_client):
        """Test document metadata retrieval endpoint logging (placeholder implementation)."""
        response = client.get("/api/v1/ingestion/documents/doc-123")
        assert response.status_code == 501

        # Verify logging calls for placeholder
        assert mock_logger_client.log_business_event.call_count >= 2  # started and not_implemented

        # Check document metadata events
        business_calls = mock_logger_client.log_business_event.call_args_list
        metadata_started = next(
            (call for call in business_calls if call[0][0] == "document_metadata_retrieval_started"), None
        )
        not_implemented = next(
            (call for call in business_calls if call[0][0] == "document_metadata_not_implemented"), None
        )

        assert metadata_started is not None
        assert not_implemented is not None

        started_data = metadata_started[0][1]
        assert started_data["document_id"] == "doc-123"
        assert started_data["operation"] == "ingested_document_metadata"

        not_impl_data = not_implemented[0][1]
        assert not_impl_data["document_id"] == "doc-123"
        assert not_impl_data["implementation_status"] == "placeholder"
        assert not_impl_data["feature_planned"] is True

    @pytest.mark.asyncio
    async def test_ingestion_sources_listing_logging_success(self, client, mock_logger_client):
        """Test ingestion sources listing endpoint logging on success."""
        response = client.get("/api/v1/ingestion/sources")
        assert response.status_code == 200

        # Verify logging calls
        assert mock_logger_client.log_business_event.call_count >= 2  # started and listed
        assert mock_logger_client.log_performance_metric.call_count == 1

        # Check ingestion sources listing events
        business_calls = mock_logger_client.log_business_event.call_args_list
        sources_started = next(
            (call for call in business_calls if call[0][0] == "ingestion_sources_listing_started"), None
        )
        sources_listed = next((call for call in business_calls if call[0][0] == "ingestion_sources_listed"), None)

        assert sources_started is not None
        assert sources_listed is not None

        started_data = sources_started[0][1]
        assert started_data["operation"] == "ingestion_capability_discovery"
        assert started_data["source_inventory"] is True

        listed_data = sources_listed[0][1]
        assert listed_data["sources_returned"] == 4  # GitHub, GitLab, Jira, Confluence
        assert listed_data["source_types"] == 4
        assert listed_data["capability_inventory_complete"] is True

    @pytest.mark.asyncio
    async def test_ingestion_cancellation_logging_placeholder(self, client, mock_logger_client):
        """Test ingestion cancellation endpoint logging (placeholder implementation)."""
        response = client.delete("/api/v1/ingestion/ingest/ingestion-123")
        assert response.status_code == 501

        # Verify logging calls for placeholder
        assert mock_logger_client.log_business_event.call_count >= 2  # started and not_implemented

        # Check ingestion cancellation events
        business_calls = mock_logger_client.log_business_event.call_args_list
        cancellation_started = next(
            (call for call in business_calls if call[0][0] == "ingestion_cancellation_started"), None
        )
        not_implemented = next(
            (call for call in business_calls if call[0][0] == "ingestion_cancellation_not_implemented"), None
        )

        assert cancellation_started is not None
        assert not_implemented is not None

        started_data = cancellation_started[0][1]
        assert started_data["ingestion_id"] == "ingestion-123"
        assert started_data["control_type"] == "workflow_cancellation"
        assert started_data["graceful_shutdown"] is True

        not_impl_data = not_implemented[0][1]
        assert not_impl_data["ingestion_id"] == "ingestion-123"
        assert not_impl_data["implementation_status"] == "placeholder"

    @pytest.mark.asyncio
    async def test_ingestion_workflow_creation_logging_failure(self, client, mock_logger_client):
        """Test ingestion workflow creation endpoint logging on failure."""
        with patch("services.orchestrator.presentation.api.ingestion.routes.container") as mock_container:
            mock_container.start_ingestion_use_case.execute.side_effect = ValueError("Invalid source URL format")

            ingestion_request = {"source_url": "invalid-url", "source_type": "github"}
            response = client.post("/api/v1/ingestion/ingest", json=ingestion_request)
            assert response.status_code == 500

            # Verify error logging
            assert mock_logger_client.log_error.call_count == 1
            assert mock_logger_client.log_business_event.call_count >= 2  # started and failed

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert "Ingestion workflow creation failed" in error_call[0][0]
            assert error_call[0][1]["error_type"] == "ValueError"
            assert error_call[0][1]["source_url"] == "invalid-url"

            # Check failure event
            business_calls = mock_logger_client.log_business_event.call_args_list
            workflow_failed = next(
                (call for call in business_calls if call[0][0] == "ingestion_workflow_creation_failed"), None
            )
            assert workflow_failed is not None

    @pytest.mark.asyncio
    async def test_request_ids_generated_uniquely(self, client, mock_logger_client):
        """Test that all endpoints generate unique request IDs."""
        request_ids = set()

        with patch("services.orchestrator.presentation.api.ingestion.routes.container") as mock_container:
            # Mock all the use cases to return success
            mock_result = {"ingestion_id": "test", "status": "processing", "ingestions": [], "total": 0}
            mock_container.start_ingestion_use_case.execute.return_value = mock_result
            mock_container.get_ingestion_status_use_case.execute.return_value = mock_result
            mock_container.list_ingestions_use_case.execute.return_value = mock_result

            # Make requests to different endpoints
            client.post(
                "/api/v1/ingestion/ingest", json={"source_url": "https://github.com/test/repo", "source_type": "github"}
            )
            client.get("/api/v1/ingestion/ingest/test-ingestion")
            client.get("/api/v1/ingestion/ingest?limit=10")
            client.get("/api/v1/ingestion/documents/doc-123")
            client.get("/api/v1/ingestion/sources")
            client.delete("/api/v1/ingestion/ingest/test-ingestion")

            # Collect request IDs from business events
            business_calls = mock_logger_client.log_business_event.call_args_list
            for call in business_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get("request_id")
                    if request_id:
                        request_ids.add(request_id)

        # Should have collected multiple unique request IDs
        assert len(request_ids) >= 6  # At least one per endpoint

        # All request IDs should follow expected patterns
        for request_id in request_ids:
            assert any(
                prefix in request_id
                for prefix in [
                    "ingestion_start_",
                    "ingestion_status_",
                    "ingestions_list_",
                    "document_metadata_",
                    "ingestion_sources_",
                    "ingestion_cancel_",
                ]
            )

    @pytest.mark.asyncio
    async def test_performance_metrics_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        mock_result = {"ingestion_id": "test", "status": "processing"}

        with patch("services.orchestrator.presentation.api.ingestion.routes.container") as mock_container:
            mock_container.get_ingestion_status_use_case.execute.return_value = mock_result

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            response = client.get("/api/v1/ingestion/ingest/test-ingestion")
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            status_perf = next((call for call in perf_calls if call[0][0] == "ingestion_status_retrieval"), None)
            assert status_perf is not None

            processing_time = status_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Patch get_logger_client to return None
        with patch("services.orchestrator.presentation.api.ingestion.routes.get_logger_client") as mock_get_client:
            mock_get_client.return_value = None

            with patch("services.orchestrator.presentation.api.ingestion.routes.container") as mock_container:
                mock_container.list_ingestions_use_case.execute.return_value = {"ingestions": []}

                # Make request - should still work without logging
                response = client.get("/api/v1/ingestion/ingest?limit=10")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_business_events_comprehensive_coverage(self, client, mock_logger_client):
        """Test that all major business events are logged across ingestion endpoints."""
        expected_events = {
            # Ingestion workflow events
            "ingestion_workflow_started",
            "ingestion_workflow_created",
            "ingestion_workflow_creation_failed",
            # Ingestion status events
            "ingestion_status_retrieval_started",
            "ingestion_status_retrieved",
            "ingestion_not_found",
            "ingestion_status_retrieval_failed",
            # Ingestion listing events
            "ingestion_listing_started",
            "ingestion_listing_completed",
            "ingestion_listing_failed",
            # Document metadata events
            "document_metadata_retrieval_started",
            "document_metadata_not_implemented",
            "document_metadata_retrieval_failed",
            # Ingestion sources events
            "ingestion_sources_listing_started",
            "ingestion_sources_listed",
            "ingestion_sources_listing_failed",
            # Ingestion control events
            "ingestion_cancellation_started",
            "ingestion_cancellation_not_implemented",
            "ingestion_cancellation_failed",
        }

        # Test a representative sample of endpoints to verify event logging
        with patch("services.orchestrator.presentation.api.ingestion.routes.container") as mock_container:
            # Mock successful responses
            mock_result = {"ingestion_id": "test", "status": "processing", "ingestions": []}
            mock_container.start_ingestion_use_case.execute.return_value = mock_result
            mock_container.get_ingestion_status_use_case.execute.return_value = mock_result
            mock_container.list_ingestions_use_case.execute.return_value = mock_result

            # Make requests to key endpoints
            client.post(
                "/api/v1/ingestion/ingest", json={"source_url": "https://github.com/test/repo", "source_type": "github"}
            )
            client.get("/api/v1/ingestion/ingest/test-ingestion")
            client.get("/api/v1/ingestion/ingest?limit=10")
            client.get("/api/v1/ingestion/documents/doc-123")
            client.get("/api/v1/ingestion/sources")
            client.delete("/api/v1/ingestion/ingest/test-ingestion")

            # Check which events were actually logged
            business_calls = mock_logger_client.log_business_event.call_args_list
            logged_events = {call[0][0] for call in business_calls}

            # Verify we logged some key events (not all, as some require specific conditions)
            key_events_logged = logged_events.intersection(
                {
                    "ingestion_workflow_started",
                    "ingestion_workflow_created",
                    "ingestion_status_retrieval_started",
                    "ingestion_status_retrieved",
                    "ingestion_listing_started",
                    "ingestion_listing_completed",
                    "document_metadata_retrieval_started",
                    "document_metadata_not_implemented",
                    "ingestion_sources_listing_started",
                    "ingestion_sources_listed",
                    "ingestion_cancellation_started",
                    "ingestion_cancellation_not_implemented",
                }
            )

            assert len(key_events_logged) >= 12  # Should have logged most key events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
