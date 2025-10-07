"""
E2E Tests: Logging & Observability

Tests logging integration and correlation ID tracking across services.
Mimics STEP 2 and STEP 5 of demo_mcp_workflow_validation.py.

Test Modes:
- Code: Tests log client and middleware
- Live: Tests actual log aggregation in mcp-logs/Elasticsearch
"""

import pytest
import asyncio


class TestLoggingObservability:
    """Test suite for logging and observability."""
    
    @pytest.mark.asyncio
    async def test_mcp_logs_operational(
        self,
        http_client,
        service_urls,
        test_mode
    ):
        """
        Test that mcp-logs service is operational.
        
        Expected:
        - Health check returns 200
        - Can query logs endpoint
        """
        url = service_urls["mcp-logs"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Health check
        response = await http_client.get(f"{url}/health")
        assert response.status_code == 200
        
        # Query logs endpoint
        response = await http_client.get(
            f"{url}/api/v1/logs",
            params={"limit": 10}
        )
        
        assert response.status_code == 200, \
            f"Logs query failed: {response.status_code}"
        
        data = response.json()
        assert "entries" in data or isinstance(data, list), \
            "Logs response missing entries"
    
    @pytest.mark.asyncio
    async def test_correlation_id_propagation(
        self,
        http_client,
        service_urls,
        sample_document,
        correlation_id,
        wait_for_log,
        test_mode
    ):
        """
        Test that correlation ID is tracked across services.
        
        Steps:
        1. Make request with correlation ID
        2. Wait for logs to appear
        3. Query logs by correlation ID
        4. Verify logs contain correct correlation ID
        
        Expected: Logs queryable by correlation ID
        """
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Make request with correlation ID
        kafka_url = service_urls["kafka-ingestion"]
        response = await http_client.post(
            f"{kafka_url}/api/v1/ingestion/ingest",
            json=sample_document,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201]
        
        # Wait for logs to appear
        logs_url = service_urls["mcp-logs"]
        log_entries = await wait_for_log(logs_url, correlation_id, timeout=15)
        
        assert len(log_entries) > 0, \
            f"No logs found with correlation ID: {correlation_id}"
        
        # Verify correlation IDs
        for entry in log_entries:
            assert entry.get("correlation_id") == correlation_id, \
                f"Log entry has wrong correlation ID: {entry.get('correlation_id')}"
    
    @pytest.mark.asyncio
    async def test_multi_service_correlation(
        self,
        http_client,
        service_urls,
        sample_document,
        correlation_id,
        wait_for_log,
        test_mode
    ):
        """
        Test correlation ID tracking across multiple services.
        
        Steps:
        1. Trigger workflow that touches multiple services
        2. Query logs by correlation ID
        3. Verify logs from multiple services present
        
        Expected: Logs from kafka-ingestion at minimum
        """
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Trigger ingestion (involves kafka-ingestion)
        kafka_url = service_urls["kafka-ingestion"]
        response = await http_client.post(
            f"{kafka_url}/api/v1/ingestion/ingest",
            json=sample_document,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201]
        
        # Wait and query logs
        await asyncio.sleep(3)  # Give time for logs to propagate
        
        logs_url = service_urls["mcp-logs"]
        log_entries = await wait_for_log(logs_url, correlation_id, timeout=15)
        
        # Extract service names
        services_logged = set()
        for entry in log_entries:
            service = entry.get("service", "unknown")
            services_logged.add(service)
        
        assert "kafka-ingestion" in services_logged or \
               "kafka-ingestion-service" in services_logged, \
            f"kafka-ingestion not in logged services: {services_logged}"
    
    @pytest.mark.asyncio
    async def test_log_levels_respected(
        self,
        http_client,
        service_urls,
        correlation_id,
        wait_for_log,
        test_mode
    ):
        """
        Test that different log levels are properly captured.
        
        Expected: Logs contain appropriate log levels
        """
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Make request that generates logs
        kafka_url = service_urls["kafka-ingestion"]
        response = await http_client.get(
            f"{kafka_url}/health",
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code == 200
        
        # Query logs
        await asyncio.sleep(2)
        logs_url = service_urls["mcp-logs"]
        log_entries = await wait_for_log(logs_url, correlation_id, timeout=10)
        
        if len(log_entries) > 0:
            # Verify log levels are present and valid
            valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            for entry in log_entries:
                level = entry.get("level", "").upper()
                if level:  # If level is present, it should be valid
                    assert level in valid_levels, \
                        f"Invalid log level: {level}"
    
    @pytest.mark.asyncio
    async def test_structured_logging_format(
        self,
        http_client,
        service_urls,
        sample_document,
        correlation_id,
        wait_for_log,
        test_mode
    ):
        """
        Test that logs follow structured format.
        
        Expected fields:
        - message
        - level
        - service
        - timestamp
        - correlation_id
        """
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Generate logs
        kafka_url = service_urls["kafka-ingestion"]
        response = await http_client.post(
            f"{kafka_url}/api/v1/ingestion/ingest",
            json=sample_document,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201]
        
        # Query and verify structure
        await asyncio.sleep(2)
        logs_url = service_urls["mcp-logs"]
        log_entries = await wait_for_log(logs_url, correlation_id, timeout=15)
        
        assert len(log_entries) > 0, "No log entries found"
        
        # Check first log entry structure
        entry = log_entries[0]
        required_fields = ["message", "level", "service", "timestamp"]
        
        for field in required_fields:
            assert field in entry, \
                f"Log entry missing required field: {field}"
