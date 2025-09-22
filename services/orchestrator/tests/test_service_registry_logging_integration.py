"""Tests for Orchestrator Service Registry Routes logging integration with LogCollectorClient."""

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


class TestOrchestratorServiceRegistryLoggingIntegration:
    """Test Orchestrator Service Registry routes logging integration with LogCollectorClient."""

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
        # Patch the get_logger_client function in the service registry routes
        with patch(
            "services.orchestrator.presentation.api.service_registry.routes.get_logger_client"
        ) as mock_get_client:
            mock_get_client.return_value = mock_logger_client
            yield

    @pytest.mark.asyncio
    async def test_service_registration_logging_success(self, client, mock_logger_client):
        """Test service registration endpoint logging on success."""
        mock_result = type(
            "MockResult",
            (),
            {
                "is_failure": lambda: False,
                "data": {"id": "test-service-123", "name": "test-service", "status": "registered"},
            },
        )()

        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            mock_container.register_service_use_case.execute.return_value = mock_result

            registration_request = {
                "service_name": "test-service",
                "service_url": "http://test-service:8080",
                "capabilities": ["llm-inference", "document-processing"],
                "metadata": {"version": "1.0.0"},
            }
            response = client.post("/api/v1/service-registry/register", json=registration_request)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and registered
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check service registration events
            business_calls = mock_logger_client.log_business_event.call_args_list
            registration_started = next(
                (call for call in business_calls if call[0][0] == "service_registration_started"), None
            )
            service_registered = next((call for call in business_calls if call[0][0] == "service_registered"), None)

            assert registration_started is not None
            assert service_registered is not None

            started_data = registration_started[0][1]
            assert started_data["service_name"] == "test-service"
            assert started_data["service_url"] == "http://test-service:8080"
            assert started_data["capabilities_count"] == 2
            assert started_data["metadata_provided"] is True

            registered_data = service_registered[0][1]
            assert registered_data["service_name"] == "test-service"
            assert registered_data["service_url"] == "http://test-service:8080"
            assert registered_data["capabilities_registered"] == 2
            assert registered_data["registry_entry_created"] is True

    @pytest.mark.asyncio
    async def test_service_registration_logging_validation_failure(self, client, mock_logger_client):
        """Test service registration endpoint logging when validation fails."""
        mock_result = type(
            "MockResult", (), {"is_failure": lambda: True, "get_errors_string": lambda: "Service name already exists"}
        )()

        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            mock_container.register_service_use_case.execute.return_value = mock_result

            registration_request = {
                "service_name": "existing-service",
                "service_url": "http://existing-service:8080",
                "capabilities": ["llm-inference"],
            }
            response = client.post("/api/v1/service-registry/register", json=registration_request)
            assert response.status_code == 400

            # Verify error logging
            assert mock_logger_client.log_business_event.call_count >= 2  # started and validation failed

            # Check validation failure event
            business_calls = mock_logger_client.log_business_event.call_args_list
            validation_failed = next(
                (call for call in business_calls if call[0][0] == "service_registration_validation_failed"), None
            )
            assert validation_failed is not None

            failed_data = validation_failed[0][1]
            assert failed_data["service_name"] == "existing-service"
            assert "Service name already exists" in failed_data["validation_errors"]

    @pytest.mark.asyncio
    async def test_service_unregistration_logging_success(self, client, mock_logger_client):
        """Test service unregistration endpoint logging on success."""
        mock_result = type("MockResult", (), {"is_failure": lambda: False})()

        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            mock_container.unregister_service_use_case.execute.return_value = mock_result

            unregistration_request = {"service_name": "test-service"}
            response = client.delete("/api/v1/service-registry/unregister", json=unregistration_request)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and unregistered
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check service unregistration events
            business_calls = mock_logger_client.log_business_event.call_args_list
            unregistration_started = next(
                (call for call in business_calls if call[0][0] == "service_unregistration_started"), None
            )
            service_unregistered = next((call for call in business_calls if call[0][0] == "service_unregistered"), None)

            assert unregistration_started is not None
            assert service_unregistered is not None

            started_data = unregistration_started[0][1]
            assert started_data["service_name"] == "test-service"
            assert started_data["unregistration_type"] == "explicit_removal"

            unregistered_data = service_unregistered[0][1]
            assert unregistered_data["service_name"] == "test-service"
            assert unregistered_data["registry_entry_removed"] is True
            assert unregistered_data["cleanup_completed"] is True

    @pytest.mark.asyncio
    async def test_service_info_retrieval_logging_success(self, client, mock_logger_client):
        """Test service information retrieval endpoint logging on success."""
        mock_result = type(
            "MockResult",
            (),
            {
                "is_failure": lambda: False,
                "data": {
                    "id": "test-service-123",
                    "name": "test-service",
                    "category": "ai-service",
                    "capabilities": ["llm-inference", "embedding"],
                    "status": "active",
                },
            },
        )()

        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            mock_container.get_service_use_case.execute.return_value = mock_result

            response = client.get("/api/v1/service-registry/services/test-service")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and retrieved
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check service info retrieved event
            business_calls = mock_logger_client.log_business_event.call_args_list
            info_retrieved = next((call for call in business_calls if call[0][0] == "service_info_retrieved"), None)
            assert info_retrieved is not None

            retrieved_data = info_retrieved[0][1]
            assert retrieved_data["service_name"] == "test-service"
            assert retrieved_data["service_category"] == "ai-service"
            assert retrieved_data["capabilities_count"] == 2
            assert retrieved_data["service_status"] == "active"

    @pytest.mark.asyncio
    async def test_service_info_retrieval_logging_not_found(self, client, mock_logger_client):
        """Test service information retrieval endpoint logging when service not found."""
        mock_result = type(
            "MockResult", (), {"is_failure": lambda: True, "get_errors_string": lambda: "Service not found"}
        )()

        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            mock_container.get_service_use_case.execute.return_value = mock_result

            response = client.get("/api/v1/service-registry/services/nonexistent-service")
            assert response.status_code == 404

            # Verify logging calls
            business_calls = mock_logger_client.log_business_event.call_args_list
            service_not_found = next((call for call in business_calls if call[0][0] == "service_not_found"), None)
            assert service_not_found is not None

            not_found_data = service_not_found[0][1]
            assert not_found_data["service_name"] == "nonexistent-service"
            assert not_found_data["query_result"] == "not_found"

    @pytest.mark.asyncio
    async def test_service_listing_logging_with_filters(self, client, mock_logger_client):
        """Test service listing endpoint logging with various filters."""
        mock_result = type(
            "MockResult",
            (),
            {
                "is_failure": lambda: False,
                "data": type(
                    "MockData",
                    (),
                    {
                        "services": [
                            {"name": "ai-service-1", "category": "ai"},
                            {"name": "data-service-1", "category": "data"},
                        ],
                        "total": 2,
                    },
                )(),
            },
        )()

        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            mock_container.list_services_use_case.execute.return_value = mock_result

            response = client.get("/api/v1/service-registry/services?category=ai&capability=llm-inference&limit=10")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and completed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check service listing events
            business_calls = mock_logger_client.log_business_event.call_args_list
            listing_started = next((call for call in business_calls if call[0][0] == "service_listing_started"), None)
            listing_completed = next(
                (call for call in business_calls if call[0][0] == "service_listing_completed"), None
            )

            assert listing_started is not None
            assert listing_completed is not None

            started_data = listing_started[0][1]
            assert started_data["filters_applied"] is True
            assert started_data["category_filter"] == "ai"
            assert started_data["capability_filter"] == "llm-inference"
            assert started_data["limit"] == 10

            completed_data = listing_completed[0][1]
            assert completed_data["services_returned"] == 2
            assert completed_data["filters_applied"] is True
            assert completed_data["total_available"] == 2

    @pytest.mark.asyncio
    async def test_openapi_polling_logging_initiation(self, client, mock_logger_client):
        """Test OpenAPI polling endpoint logging on initiation."""
        polling_request = {"service_urls": ["http://service1:8080", "http://service2:8080"], "force_refresh": True}
        response = client.post("/api/v1/service-registry/poll-openapi", json=polling_request)
        assert response.status_code == 200

        # Verify logging calls
        assert mock_logger_client.log_business_event.call_count >= 2  # started and initiated
        assert mock_logger_client.log_performance_metric.call_count == 1

        # Check OpenAPI polling events
        business_calls = mock_logger_client.log_business_event.call_args_list
        polling_started = next((call for call in business_calls if call[0][0] == "openapi_polling_started"), None)
        polling_initiated = next((call for call in business_calls if call[0][0] == "openapi_polling_initiated"), None)

        assert polling_started is not None
        assert polling_initiated is not None

        started_data = polling_started[0][1]
        assert started_data["services_to_poll"] == 2
        assert started_data["force_refresh"] is True
        assert started_data["polling_type"] == "bulk_openapi_collection"

        initiated_data = polling_initiated[0][1]
        assert initiated_data["services_targeted"] == 2
        assert initiated_data["force_refresh"] is True
        assert initiated_data["polling_status"] == "initiated"

    @pytest.mark.asyncio
    async def test_capabilities_listing_logging_success(self, client, mock_logger_client):
        """Test capabilities listing endpoint logging on success."""
        response = client.get("/api/v1/service-registry/capabilities")
        assert response.status_code == 200

        # Verify logging calls
        assert mock_logger_client.log_business_event.call_count >= 2  # started and listed
        assert mock_logger_client.log_performance_metric.call_count == 1

        # Check capabilities listing events
        business_calls = mock_logger_client.log_business_event.call_args_list
        listing_started = next((call for call in business_calls if call[0][0] == "capabilities_listing_started"), None)
        capabilities_listed = next((call for call in business_calls if call[0][0] == "capabilities_listed"), None)

        assert listing_started is not None
        assert capabilities_listed is not None

        listed_data = capabilities_listed[0][1]
        assert listed_data["capabilities_returned"] == 10  # Mock capabilities count
        assert listed_data["capability_types"] == 10
        assert listed_data["registry_services_analyzed"] == 0

    @pytest.mark.asyncio
    async def test_registry_health_check_logging_success(self, client, mock_logger_client):
        """Test registry health check endpoint logging on success."""
        mock_services_result = type(
            "MockResult",
            (),
            {
                "is_success": lambda: True,
                "data": type("MockData", (), {"services": [{"name": "service1"}, {"name": "service2"}]})(),
            },
        )()

        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            mock_container.list_services_use_case.execute.return_value = mock_services_result

            response = client.get("/api/v1/service-registry/health")
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # started and assessed
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check registry health events
            business_calls = mock_logger_client.log_business_event.call_args_list
            health_assessed = next((call for call in business_calls if call[0][0] == "registry_health_assessed"), None)
            assert health_assessed is not None

            assessed_data = health_assessed[0][1]
            assert assessed_data["registry_status"] == "healthy"
            assert assessed_data["total_services_registered"] == 2
            assert assessed_data["registry_operational"] is True

    @pytest.mark.asyncio
    async def test_service_ping_logging_success(self, client, mock_logger_client):
        """Test service ping endpoint logging on success."""
        response = client.post("/api/v1/service-registry/services/test-service/ping")
        assert response.status_code == 200

        # Verify logging calls
        assert mock_logger_client.log_business_event.call_count >= 2  # started and pinged
        assert mock_logger_client.log_performance_metric.call_count == 1

        # Check service ping events
        business_calls = mock_logger_client.log_business_event.call_args_list
        service_pinged = next((call for call in business_calls if call[0][0] == "service_pinged"), None)
        assert service_pinged is not None

        pinged_data = service_pinged[0][1]
        assert pinged_data["service_name"] == "test-service"
        assert pinged_data["service_status"] == "reachable"
        assert pinged_data["response_time_ms"] == 150
        assert pinged_data["availability_confirmed"] is True

    @pytest.mark.asyncio
    async def test_request_ids_generated_uniquely(self, client, mock_logger_client):
        """Test that all endpoints generate unique request IDs."""
        request_ids = set()

        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            # Mock all the use cases to return success
            mock_result = type(
                "MockResult",
                (),
                {"is_failure": lambda: False, "data": {"id": "test", "name": "test"}, "is_success": lambda: True},
            )()

            mock_services_result = type(
                "MockResult", (), {"is_success": lambda: True, "data": type("MockData", (), {"services": []})()}
            )()

            mock_container.register_service_use_case.execute.return_value = mock_result
            mock_container.unregister_service_use_case.execute.return_value = mock_result
            mock_container.get_service_use_case.execute.return_value = mock_result
            mock_container.list_services_use_case.execute.return_value = mock_result

            # Make requests to different endpoints
            client.post(
                "/api/v1/service-registry/register",
                json={"service_name": "test1", "service_url": "http://test1:8080", "capabilities": []},
            )
            client.delete("/api/v1/service-registry/unregister", json={"service_name": "test1"})
            client.get("/api/v1/service-registry/services/test1")
            client.get("/api/v1/service-registry/services?limit=10")
            client.post("/api/v1/service-registry/poll-openapi", json={"service_urls": ["http://test:8080"]})
            client.get("/api/v1/service-registry/capabilities")
            client.get("/api/v1/service-registry/health")
            client.post("/api/v1/service-registry/services/test1/ping")

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
                    "service_register_",
                    "service_unregister_",
                    "service_get_",
                    "services_list_",
                    "openapi_poll_",
                    "capabilities_list_",
                    "registry_health_",
                    "service_ping_",
                ]
            )

    @pytest.mark.asyncio
    async def test_performance_metrics_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        mock_result = type("MockResult", (), {"is_failure": lambda: False, "data": {"id": "test", "name": "test"}})()

        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            mock_container.get_service_use_case.execute.return_value = mock_result

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            response = client.get("/api/v1/service-registry/services/test-service")
            assert response.status_code == 200

            # Check performance metric
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            service_info_perf = next((call for call in perf_calls if call[0][0] == "service_info_retrieval"), None)
            assert service_info_perf is not None

            processing_time = service_info_perf[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_error_context_preservation(self, client, mock_logger_client):
        """Test that error context is properly preserved in logging."""
        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            mock_container.register_service_use_case.execute.side_effect = ConnectionError("Database unreachable")

            registration_request = {
                "service_name": "test-service",
                "service_url": "http://test-service:8080",
                "capabilities": ["test"],
            }
            response = client.post("/api/v1/service-registry/register", json=registration_request)
            assert response.status_code == 500

            # Check that error logging preserves context
            error_calls = mock_logger_client.log_error.call_args_list
            assert len(error_calls) > 0

            error_call = error_calls[0]
            error_data = error_call[0][1]
            assert error_data["error_type"] == "ConnectionError"
            assert "operation" in error_data
            assert "service_name" in error_data
            assert "response_time_seconds" in error_data
            assert "request_id" in error_data

    @pytest.mark.asyncio
    async def test_business_events_comprehensive_coverage(self, client, mock_logger_client):
        """Test that all major business events are logged across service registry endpoints."""
        expected_events = {
            # Service registration events
            "service_registration_started",
            "service_registered",
            "service_registration_validation_failed",
            "service_registration_failed",
            # Service unregistration events
            "service_unregistration_started",
            "service_unregistered",
            "service_unregistration_validation_failed",
            "service_unregistration_failed",
            # Service discovery events
            "service_info_retrieval_started",
            "service_info_retrieved",
            "service_not_found",
            "service_info_retrieval_failed",
            "service_listing_started",
            "service_listing_completed",
            "service_listing_validation_failed",
            "service_listing_failed",
            # OpenAPI polling events
            "openapi_polling_started",
            "openapi_polling_initiated",
            "openapi_polling_failed",
            # Capabilities discovery events
            "capabilities_listing_started",
            "capabilities_listed",
            "capabilities_listing_failed",
            # Registry monitoring events
            "registry_health_check_started",
            "registry_health_assessed",
            "registry_health_check_failed",
            # Service health events
            "service_ping_started",
            "service_pinged",
            "service_ping_failed",
        }

        # Test a representative sample of endpoints to verify event logging
        with patch("services.orchestrator.presentation.api.service_registry.routes.container") as mock_container:
            # Mock successful responses
            mock_result = type(
                "MockResult",
                (),
                {
                    "is_failure": lambda: False,
                    "data": {"id": "test", "name": "test", "capabilities": ["test"]},
                    "is_success": lambda: True,
                },
            )()

            mock_services_result = type(
                "MockResult",
                (),
                {"is_success": lambda: True, "data": type("MockData", (), {"services": [], "total": 0})()},
            )()

            mock_container.register_service_use_case.execute.return_value = mock_result
            mock_container.get_service_use_case.execute.return_value = mock_result
            mock_container.list_services_use_case.execute.return_value = mock_services_result

            # Make requests to key endpoints
            client.post(
                "/api/v1/service-registry/register",
                json={"service_name": "test1", "service_url": "http://test1:8080", "capabilities": ["test"]},
            )
            client.get("/api/v1/service-registry/services/test1")
            client.get("/api/v1/service-registry/services")
            client.post("/api/v1/service-registry/poll-openapi", json={"service_urls": ["http://test:8080"]})
            client.get("/api/v1/service-registry/capabilities")
            client.get("/api/v1/service-registry/health")
            client.post("/api/v1/service-registry/services/test1/ping")

            # Check which events were actually logged
            business_calls = mock_logger_client.log_business_event.call_args_list
            logged_events = {call[0][0] for call in business_calls}

            # Verify we logged some key events (not all, as some require specific conditions)
            key_events_logged = logged_events.intersection(
                {
                    "service_registration_started",
                    "service_registered",
                    "service_info_retrieval_started",
                    "service_info_retrieved",
                    "service_listing_started",
                    "service_listing_completed",
                    "openapi_polling_started",
                    "openapi_polling_initiated",
                    "capabilities_listing_started",
                    "capabilities_listed",
                    "registry_health_check_started",
                    "registry_health_assessed",
                    "service_ping_started",
                    "service_pinged",
                }
            )

            assert len(key_events_logged) >= 12  # Should have logged most key events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
